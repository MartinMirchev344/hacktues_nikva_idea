import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
  SafeAreaView,
  Platform,
  Image,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Audio } from 'expo-av';
import { Redirect, useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../context/auth-context';
import {
  getAttemptDetail,
  createAttempt,
  submitAttempt,
  verifySign,
  verifySignWeb,
  getMyAttempts,
  predictAlphabetPhoto,
  predictAlphabetPhotoWeb,
  AlphabetPrediction,
  VerifyResult,
} from '../../lib/auth-api';
import { palette } from '../../constants/colors';
import { ScreenBackButton } from '../../components/screen-back-button';
import { getVidref } from '../../lib/signasl-map';

type Phase = 'idle' | 'recording' | 'uploading' | 'results';
type QuizPhase = 'answering' | 'results';

function normalizeSignText(value: string | null | undefined) {
  return (value ?? '')
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ');
}

function formatSignText(value: string | null | undefined) {
  const normalized = normalizeSignText(value);
  if (!normalized) {
    return 'Unknown sign';
  }

  return normalized.replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function isAlphabetDetectionError(message: string) {
  const normalized = message.toLowerCase();
  return (
    normalized.includes('no hand detected') ||
    normalized.includes('could not identify the hand sign')
  );
}

function getAlphabetDetectionWarning(message: string) {
  if (message.toLowerCase().includes('no hand detected')) {
    return 'The photo was taken, but no hand sign was detected. Keep your whole hand inside the frame, use good lighting, and try again.';
  }

  return 'The photo was taken, but the sign could not be recognized. Try again with a clearer handshape, better lighting, or a slightly different angle.';
}

export default function Exercise() {
  const router = useRouter();
  const { id, isLastExercise, exerciseQueue, queueIndex } = useLocalSearchParams<{
    id: string;
    isLastExercise?: string;
    exerciseQueue?: string;
    queueIndex?: string;
  }>();
  const { auth, isHydrating, updateUserStats } = useAuth();

  const [attempt, setAttempt] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Quiz mode state
  const [quizPhase, setQuizPhase] = useState<QuizPhase>('answering');
  const [quizAnswer, setQuizAnswer] = useState('');
  const [quizCorrect, setQuizCorrect] = useState(false);

  // Alphabet photo mode state
  const [alphabetPrediction, setAlphabetPrediction] = useState<AlphabetPrediction | null>(null);
  const [capturedPhotoUri, setCapturedPhotoUri] = useState<string | null>(null);
  const [alphabetCaptureNotice, setAlphabetCaptureNotice] = useState<string | null>(null);
  const [isWebCameraReady, setIsWebCameraReady] = useState(Platform.OS !== 'web');

  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView | null>(null);

  // Web-specific recording refs
  const webVideoRef = useRef<any>(null);
  const webStreamRef = useRef<MediaStream | null>(null);
  const webRecorderRef = useRef<MediaRecorder | null>(null);
  const webChunksRef = useRef<Blob[]>([]);

  const attachWebVideoRef = useCallback((node: HTMLVideoElement | null) => {
    webVideoRef.current = node;
    setIsWebCameraReady(false);

    if (node && webStreamRef.current) {
      node.srcObject = webStreamRef.current;
      node.play?.().catch(() => {});
    }
  }, []);

  const waitForWebVideoReady = useCallback((video: HTMLVideoElement) => {
    if (video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0) {
      setIsWebCameraReady(true);
      return Promise.resolve();
    }

    setIsWebCameraReady(false);

    return new Promise<void>((resolve, reject) => {
      let finished = false;

      const cleanup = () => {
        if (finished) return;
        finished = true;
        window.clearTimeout(timeoutId);
        video.removeEventListener('loadedmetadata', tryResolve);
        video.removeEventListener('canplay', tryResolve);
        video.removeEventListener('playing', tryResolve);
      };

      const tryResolve = () => {
        if (video.videoWidth > 0 && video.videoHeight > 0) {
          setIsWebCameraReady(true);
          cleanup();
          resolve();
        }
      };

      const timeoutId = window.setTimeout(() => {
        cleanup();
        reject(new Error('Camera is still starting. Please wait a moment and try again.'));
      }, 2500);

      video.addEventListener('loadedmetadata', tryResolve);
      video.addEventListener('canplay', tryResolve);
      video.addEventListener('playing', tryResolve);
      video.play?.().catch(() => {});
      tryResolve();
    });
  }, []);

  useEffect(() => {
    if (Platform.OS !== 'web') return;
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
      .then(stream => {
        webStreamRef.current = stream;
        if (webVideoRef.current) {
          webVideoRef.current.srcObject = stream;
          webVideoRef.current.play?.().catch(() => {});
        }
      })
      .catch(() => {});
    return () => { webStreamRef.current?.getTracks().forEach(t => t.stop()); };
  }, []);

  const playSound = useCallback(async (type: 'correct' | 'fail' | 'lesson_complete') => {
    const sources = {
      correct: require('../../assets/sounds/correct.mp3'),
      fail: require('../../assets/sounds/fail.mp3'),
      lesson_complete: require('../../assets/sounds/lesson_complete.mp3'),
    };
    try {
      const { sound } = await Audio.Sound.createAsync(sources[type]);
      await sound.playAsync();
      sound.setOnPlaybackStatusUpdate(status => {
        if (status.isLoaded && status.didJustFinish) sound.unloadAsync();
      });
    } catch {}
  }, []);

  useEffect(() => {
    if (!auth || !id) return;
    const fetchAttempt = async () => {
      try {
        setLoading(true);
        const data = await getAttemptDetail(parseInt(id));
        setAttempt(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load exercise');
      } finally {
        setLoading(false);
      }
    };
    fetchAttempt();
  }, [auth, id]);

  const startRecording = async () => {
    if (Platform.OS === 'web') {
      const stream = webStreamRef.current;
      if (!stream) return;
      setPhase('recording');
      const recorder = new MediaRecorder(stream);
      webRecorderRef.current = recorder;
      webChunksRef.current = [];
      recorder.ondataavailable = (e: BlobEvent) => {
        if (e.data.size > 0) webChunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        const blob = new Blob(webChunksRef.current, { type: 'video/webm' });
        setPhase('uploading');
        try {
          const res = await verifySignWeb(attempt.id, blob);
          setResult(res);
          setPhase('results');
          playSound(res.is_correct ? 'correct' : 'fail');
        } catch {
          setPhase('idle');
          Alert.alert('Error', 'Failed to process video. Please try again.');
        }
      };
      recorder.start();
      setTimeout(() => { if (recorder.state === 'recording') recorder.stop(); }, 10000);
      return;
    }

    if (!cameraRef.current) return;
    setPhase('recording');
    try {
      const video = await cameraRef.current.recordAsync({ maxDuration: 10 });
      if (video?.uri) {
        setPhase('uploading');
        const res = await verifySign(attempt.id, video.uri);
        setResult(res);
        setPhase('results');
        playSound(res.is_correct ? 'correct' : 'fail');
      } else {
        setPhase('idle');
      }
    } catch (err) {
      setPhase('idle');
      Alert.alert('Error', 'Failed to process video. Please try again.');
    }
  };

  const stopRecording = () => {
    if (Platform.OS === 'web') {
      webRecorderRef.current?.stop();
      return;
    }
    cameraRef.current?.stopRecording();
  };

  const retryRecording = () => {
    setResult(null);
    setPhase('idle');
  };

  const takeAlphabetPhoto = async () => {
    if (Platform.OS === 'web') {
      const video = webVideoRef.current as HTMLVideoElement | null;
      if (!video) {
        setAlphabetCaptureNotice('The camera preview is not ready yet. Please wait a moment and try again.');
        Alert.alert('Camera unavailable', 'The camera preview is not ready yet. Please try again.');
        return;
      }
      setPhase('uploading');
      setCapturedPhotoUri(null);
      setAlphabetCaptureNotice(null);
      try {
        await waitForWebVideoReady(video);
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d')!.drawImage(video, 0, 0);
        const previewUri = canvas.toDataURL('image/jpeg');
        setCapturedPhotoUri(previewUri);
        const blob = await new Promise<Blob>((resolve, reject) => {
          canvas.toBlob((capturedBlob) => {
            if (capturedBlob) {
              resolve(capturedBlob);
              return;
            }
            reject(new Error('Failed to capture a frame from the camera.'));
          }, 'image/jpeg', 0.9);
        });
        const prediction = await predictAlphabetPhotoWeb(blob);
        setAlphabetPrediction(prediction);
        setAlphabetCaptureNotice(null);
        setPhase('results');
        const expectedSign = attempt.exercise?.expected_sign ?? '';
        playSound(prediction.predicted_letter === expectedSign ? 'correct' : 'fail');
      } catch (err) {
        setPhase('idle');
        const message = err instanceof Error ? err.message : 'Failed to process photo. Please try again.';
        setAlphabetCaptureNotice(
          isAlphabetDetectionError(message)
            ? getAlphabetDetectionWarning(message)
            : message
        );
        Alert.alert(
          isAlphabetDetectionError(message) ? 'No sign detected' : 'Try again',
          isAlphabetDetectionError(message) ? getAlphabetDetectionWarning(message) : message
        );
      }
      return;
    }
    if (!cameraRef.current) return;
    setPhase('uploading');
    setAlphabetCaptureNotice(null);
    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      if (photo?.uri) {
        setCapturedPhotoUri(photo.uri);
        const prediction = await predictAlphabetPhoto(photo.uri);
        setAlphabetPrediction(prediction);
        setAlphabetCaptureNotice(null);
        setPhase('results');
        const expectedSign = attempt.exercise?.expected_sign ?? '';
        playSound(prediction.predicted_letter === expectedSign ? 'correct' : 'fail');
      } else {
        setPhase('idle');
      }
    } catch (err) {
      setPhase('idle');
      const msg = err instanceof Error ? err.message : 'Failed to process photo. Please try again.';
      setAlphabetCaptureNotice(
        isAlphabetDetectionError(msg)
          ? getAlphabetDetectionWarning(msg)
          : msg
      );
      Alert.alert(
        isAlphabetDetectionError(msg) ? 'No sign detected' : 'Try again',
        isAlphabetDetectionError(msg) ? getAlphabetDetectionWarning(msg) : msg
      );
    }
  };

  const retryAlphabetPhoto = () => {
    setAlphabetPrediction(null);
    setCapturedPhotoUri(null);
    setAlphabetCaptureNotice(null);
    setPhase('idle');
  };

  const handleAlphabetSubmit = async () => {
    if (!alphabetPrediction) return;
    const expectedSign = attempt.exercise?.expected_sign ?? '';
    const isCorrect = alphabetPrediction.predicted_letter === expectedSign;
    const confidence = alphabetPrediction.confidence;
    setIsSubmitting(true);
    try {
      const saved = await submitAttempt(attempt.id, {
        status: 'completed',
        accuracy_score: isCorrect ? confidence : Math.max(confidence * 0.5, 5),
        speed_score: 100,
        handshape_score: confidence,
        detected_sign: alphabetPrediction.predicted_letter,
        coach_summary: isCorrect
          ? `Correct! The model recognized "${alphabetPrediction.predicted_letter.toUpperCase()}" with ${confidence.toFixed(0)}% confidence.`
          : `The model saw "${alphabetPrediction.predicted_letter.toUpperCase()}" instead of "${expectedSign.toUpperCase()}". Try adjusting your hand position and lighting.`,
        completed_at: new Date().toISOString(),
      });
      if (saved.total_xp != null && saved.streak != null) {
        updateUserStats(saved.total_xp, saved.streak);
      }
      await advanceOrExit(isCorrect);
    } catch {
      Alert.alert('Error', 'Failed to save results. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async () => {
    if (!result) return;
    setIsSubmitting(true);
    try {
      const saved = await submitAttempt(attempt.id, {
        status: 'completed',
        accuracy_score: result.accuracy_score,
        speed_score: result.speed_score,
        handshape_score: result.handshape_score,
        detected_sign: result.detected_sign,
        coach_summary: result.coach_summary,
        feedback_items: result.feedback_items,
        completed_at: new Date().toISOString(),
      });
      if (saved.total_xp != null && saved.streak != null) {
        updateUserStats(saved.total_xp, saved.streak);
      }
      await advanceOrExit(result.is_correct);
    } catch (err) {
      Alert.alert('Error', 'Failed to save results. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const advanceOrExit = async (isCorrect: boolean) => {
    const queue: number[] = exerciseQueue ? JSON.parse(exerciseQueue) : [];
    const idx = queueIndex ? parseInt(queueIndex) : -1;

    if (queue.length > 0) {
      // Check if all exercises in the lesson are now completed
      const attempts = await getMyAttempts();
      const completedIds = new Set(
        attempts.filter(a => a.status === 'completed').map(a => a.exercise.id)
      );
      const allDone = queue.every(exId => completedIds.has(exId));
      if (allDone) await playSound('lesson_complete');
    }

    if (queue.length > 0 && idx >= 0 && idx < queue.length - 1) {
      const nextExerciseId = queue[idx + 1];
      const nextAttempt = await createAttempt(nextExerciseId);
      router.replace({
        pathname: `/exercise/${nextAttempt.id}`,
        params: { exerciseQueue, queueIndex: String(idx + 1) },
      });
    } else {
      router.back();
    }
  };

  const handleQuizSubmit = async () => {
    if (!quizAnswer.trim()) {
      Alert.alert('Error', 'Please enter an answer');
      return;
    }
    const correct =
      normalizeSignText(quizAnswer) ===
      normalizeSignText(attempt.exercise?.expected_sign);
    setQuizCorrect(correct);
    setQuizPhase('results');
    playSound(correct ? 'correct' : 'fail');
  };

  const handleQuizSave = async () => {
    setIsSubmitting(true);
    try {
      const saved = await submitAttempt(attempt.id, {
        status: 'completed',
        accuracy_score: quizCorrect ? 100 : 0,
        detected_sign: quizAnswer.trim(),
        completed_at: new Date().toISOString(),
      });
      if (saved.total_xp != null && saved.streak != null) {
        updateUserStats(saved.total_xp, saved.streak);
      }
      await advanceOrExit(quizCorrect);
    } catch {
      Alert.alert('Error', 'Failed to save results. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isHydrating) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={palette.text} />
        <Text style={styles.loadingText}>Loading exercise...</Text>
      </View>
    );
  }

  if (!auth) {
    return <Redirect href="/signup" />;
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={palette.text} />
        <Text style={styles.loadingText}>Loading exercise...</Text>
      </View>
    );
  }

  if (error || !attempt) {
    return (
      <View style={styles.center}>
        <ScreenBackButton fallbackHref="/home" style={styles.inlineBackButton} />
        <Text style={styles.errorText}>{error || 'Exercise not found'}</Text>
      </View>
    );
  }

  const isQuiz = attempt.exercise?.exercise_type === 'quiz';
  const isAlphabetExercise = !isQuiz && (attempt.exercise?.expected_sign ?? '').length === 1;

  // Already completed
  if (attempt.status !== 'in_progress') {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scroll}>
          <ScreenBackButton fallbackHref="/home" />
          <Text style={styles.title}>Exercise Complete</Text>
          <ExerciseCard attempt={attempt} />
          {attempt.accuracy_score !== null && <ScoresCard attempt={attempt} />}
          {attempt.coach_summary && <FeedbackCard attempt={attempt} />}
          <TouchableOpacity style={styles.btn} onPress={() => router.back()}>
            <Text style={styles.btnText}>Back to Lesson</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Camera permission denied
  if (!isQuiz && permission && !permission.granted) {
    return (
      <View style={styles.center}>
        <ScreenBackButton fallbackHref="/home" style={styles.inlineBackButton} />
        <Text style={styles.errorText}>Camera access is required to practice signs.</Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>Allow Camera</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (isQuiz) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scroll} bounces={false}>
          <ScreenBackButton fallbackHref="/home" />
          <ExerciseCard attempt={attempt} />

          <SignAslVideo expectedSign={attempt.exercise?.expected_sign ?? ''} />

          {quizPhase === 'answering' && (
            <>
              <Text style={styles.hint}>Watch the gesture above and type what it means</Text>
              <TextInput
                style={styles.quizInput}
                placeholder="Type the phrase or word..."
                placeholderTextColor={palette.text + '88'}
                value={quizAnswer}
                onChangeText={setQuizAnswer}
                autoCapitalize="none"
              />
              <TouchableOpacity style={styles.btn} onPress={handleQuizSubmit}>
                <Text style={styles.btnText}>Check Answer</Text>
              </TouchableOpacity>
            </>
          )}

          {quizPhase === 'results' && (
            <>
              <View style={[styles.resultBanner, quizCorrect ? styles.bannerPass : styles.bannerFail]}>
                <Text style={styles.resultIcon}>{quizCorrect ? '✓' : '✗'}</Text>
                <View>
                  <Text style={styles.resultTitle}>{quizCorrect ? 'Correct!' : 'Not quite'}</Text>
                  {!quizCorrect && (
                    <Text style={styles.resultSub}>
                      Answer: {formatSignText(attempt.exercise?.expected_sign)}
                    </Text>
                  )}
                </View>
              </View>

              <View style={styles.resultActions}>
                <TouchableOpacity
                  style={styles.retryBtn}
                  onPress={() => { setQuizAnswer(''); setQuizPhase('answering'); }}
                >
                  <Text style={styles.retryBtnText}>Try Again</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btn, styles.submitBtn, isSubmitting && styles.btnDisabled]}
                  onPress={handleQuizSave}
                  disabled={isSubmitting}
                >
                  <Text style={styles.btnText}>{isSubmitting ? 'Saving...' : 'Save & Continue'}</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ── Alphabet photo mode ────────────────────────────────────────────────────
  if (isAlphabetExercise) {
    const expectedSign = attempt.exercise?.expected_sign ?? '';
    const isCorrect = alphabetPrediction?.predicted_letter === expectedSign;
    const isAlphabetCaptureDisabled =
      phase !== 'idle' || (Platform.OS === 'web' && !isWebCameraReady);

    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scroll} bounces={false}>
          <ScreenBackButton fallbackHref="/home" />
          <ExerciseCard attempt={attempt} />

          {phase !== 'results' && (
            <View style={[styles.cameraWrapper, Platform.OS === 'web' && styles.cameraWrapperWeb]}>
              {Platform.OS === 'web' ? (
                // @ts-ignore
                <video
                  ref={attachWebVideoRef}
                  autoPlay
                  muted
                  playsInline
                  onLoadedMetadata={() => setIsWebCameraReady(true)}
                  onCanPlay={() => setIsWebCameraReady(true)}
                  onPlaying={() => setIsWebCameraReady(true)}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <CameraView ref={cameraRef} style={styles.camera} facing="front" />
              )}
              {phase === 'uploading' && capturedPhotoUri && (
                <Image source={{ uri: capturedPhotoUri }} style={[styles.camera, { position: 'absolute' }]} resizeMode="cover" />
              )}
              {phase === 'uploading' && (
                <View style={styles.uploadingOverlay}>
                  <ActivityIndicator size="large" color={palette.background} />
                  <Text style={styles.uploadingText}>Analysing your sign...</Text>
                </View>
              )}
            </View>
          )}

          {phase === 'idle' && (
            <>
              <TouchableOpacity
                style={[styles.recordBtn, isAlphabetCaptureDisabled && styles.captureBtnDisabled]}
                onPress={takeAlphabetPhoto}
                disabled={isAlphabetCaptureDisabled}
              >
                <View style={styles.photoBtnInner} />
              </TouchableOpacity>
              <Text style={styles.hint}>
                {Platform.OS === 'web' && !isWebCameraReady
                  ? 'Camera is warming up...'
                  : `Hold up the letter "${expectedSign.toUpperCase()}" and tap to take a photo`}
              </Text>
              <View style={styles.warningCard}>
                <Text style={styles.warningTitle}>Warning</Text>
                <Text style={styles.warningText}>
                  If no sign is detected, the photo was still taken. It usually means your hand was out of frame,
                  the lighting was too weak, or the handshape was unclear.
                </Text>
              </View>
              {alphabetCaptureNotice && (
                <View style={styles.captureNoticeCard}>
                  <Text style={styles.captureNoticeTitle}>Last capture</Text>
                  {capturedPhotoUri ? (
                    <Image source={{ uri: capturedPhotoUri }} style={styles.captureNoticePreview} resizeMode="cover" />
                  ) : null}
                  <Text style={styles.captureNoticeText}>{alphabetCaptureNotice}</Text>
                </View>
              )}
            </>
          )}

          {phase === 'results' && alphabetPrediction && (
            <>
              <View style={[styles.resultBanner, isCorrect ? styles.bannerPass : styles.bannerFail]}>
                <Text style={styles.resultIcon}>{isCorrect ? '✓' : '✗'}</Text>
                <View>
                  <Text style={styles.resultTitle}>{isCorrect ? 'Correct!' : 'Not quite'}</Text>
                  <Text style={styles.resultSub}>
                    Detected: {alphabetPrediction.predicted_letter.toUpperCase()} ({alphabetPrediction.confidence.toFixed(0)}%)
                  </Text>
                </View>
              </View>

              <View style={styles.predictionCard}>
                <Text style={styles.predictionEyebrow}>Model Prediction</Text>
                <Text style={styles.predictionSign}>{alphabetPrediction.predicted_letter.toUpperCase()}</Text>
                <Text style={styles.predictionConfidence}>Confidence {alphabetPrediction.confidence.toFixed(0)}%</Text>
                {alphabetPrediction.top_predictions.length > 1 && (
                  <View style={styles.alternativePredictions}>
                    <Text style={styles.alternativeTitle}>Other guesses</Text>
                    {alphabetPrediction.top_predictions.slice(1).map((p) => (
                      <View key={p.letter} style={styles.alternativeRow}>
                        <Text style={styles.alternativeSign}>{p.letter.toUpperCase()}</Text>
                        <Text style={styles.alternativeScore}>{p.confidence.toFixed(0)}%</Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>

              <View style={styles.resultActions}>
                <TouchableOpacity style={styles.retryBtn} onPress={retryAlphabetPhoto}>
                  <Text style={styles.retryBtnText}>Try Again</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.btn, styles.submitBtn, isSubmitting && styles.btnDisabled]}
                  onPress={handleAlphabetSubmit}
                  disabled={isSubmitting}
                >
                  <Text style={styles.btnText}>{isSubmitting ? 'Saving...' : 'Save & Continue'}</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ── Normal video mode ──────────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} bounces={false}>
        <ScreenBackButton fallbackHref="/home" />
        {/* Exercise prompt */}
        <ExerciseCard attempt={attempt} />

        {/* Camera + controls */}
        {phase !== 'results' && (
          <View style={[styles.cameraWrapper, Platform.OS === 'web' && styles.cameraWrapperWeb]}>
            {Platform.OS === 'web' ? (
              // @ts-ignore - web only element
              <video
                ref={attachWebVideoRef}
                autoPlay
                muted
                playsInline
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <CameraView ref={cameraRef} style={styles.camera} facing="front" mode="video" />
            )}

            {/* Recording indicator */}
            {phase === 'recording' && (
              <View style={styles.recordingBadge}>
                <View style={styles.recordingDot} />
                <Text style={styles.recordingText}>Recording...</Text>
              </View>
            )}

            {/* Uploading overlay */}
            {phase === 'uploading' && (
              <View style={styles.uploadingOverlay}>
                <ActivityIndicator size="large" color={palette.background} />
                <Text style={styles.uploadingText}>Analysing your sign...</Text>
              </View>
            )}
          </View>
        )}

        {/* Record / Stop button */}
        {phase === 'idle' && (
          <TouchableOpacity style={styles.recordBtn} onPress={startRecording}>
            <View style={styles.recordBtnInner} />
          </TouchableOpacity>
        )}
        {phase === 'recording' && (
          <TouchableOpacity style={styles.stopBtn} onPress={stopRecording}>
            <View style={styles.stopBtnInner} />
          </TouchableOpacity>
        )}
        {phase === 'idle' && (
          <Text style={styles.hint}>
            Tap the button and sign "{attempt.exercise?.expected_sign}"
          </Text>
        )}
        {phase === 'recording' && (
          <Text style={styles.hint}>Tap to stop (max 10 seconds)</Text>
        )}

        {/* Results */}
        {phase === 'results' && result && (
          <>
            <View style={[styles.resultBanner, result.is_correct ? styles.bannerPass : styles.bannerFail]}>
              <Text style={styles.resultIcon}>{result.is_correct ? '✓' : '✗'}</Text>
              <View>
                <Text style={styles.resultTitle}>
                  {result.is_correct ? 'Correct!' : 'Not quite'}
                </Text>
                {result.detected_sign ? (
                  <Text style={styles.resultSub}>
                    Detected: {result.detected_sign}
                    {result.confidence > 0 ? ` (${result.confidence.toFixed(0)}%)` : ''}
                  </Text>
                ) : null}
              </View>
            </View>

            <PredictionCard result={result} />

            <ScoresCard attempt={{
              accuracy_score: result.accuracy_score,
              speed_score: result.speed_score,
              handshape_score: result.handshape_score,
              score: (result.accuracy_score + result.speed_score + result.handshape_score) / 3,
            }} />

            {result.coach_summary ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Coach Feedback</Text>
                <Text style={styles.cardBody}>{result.coach_summary}</Text>
                {result.feedback_items.length > 0 && (
                  <View style={styles.feedbackList}>
                    {result.feedback_items.map((item, i) => (
                      <Text key={i} style={styles.feedbackItem}>• {item}</Text>
                    ))}
                  </View>
                )}
              </View>
            ) : null}

            <View style={styles.resultActions}>
              <TouchableOpacity style={styles.retryBtn} onPress={retryRecording}>
                <Text style={styles.retryBtnText}>Try Again</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btn, styles.submitBtn, isSubmitting && styles.btnDisabled]}
                onPress={handleSubmit}
                disabled={isSubmitting}
              >
                <Text style={styles.btnText}>
                  {isSubmitting ? 'Saving...' : 'Save & Continue'}
                </Text>
              </TouchableOpacity>
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function ExerciseCard({ attempt }: { attempt: any }) {
  const isQuiz = attempt.exercise?.exercise_type === 'quiz';
  return (
    <View style={styles.card}>
      <Text style={styles.prompt}>
        {attempt.exercise?.prompt || (isQuiz ? 'Watch the Sign Demo' : 'Practice this sign')}
      </Text>
      <Text style={styles.cardBody}>{attempt.exercise?.instructions}</Text>
      {!isQuiz && (
        <Text style={styles.targetSign}>
          Sign: <Text style={styles.targetSignValue}>{formatSignText(attempt.exercise?.expected_sign)}</Text>
        </Text>
      )}
    </View>
  );
}

function SignAslVideo({ expectedSign }: { expectedSign: string }) {
  const vidref = getVidref(expectedSign);

  if (!vidref) {
    return (
      <View style={styles.videoPreviewCard}>
        <Text style={styles.videoPreviewEyebrow}>Sign Demo</Text>
        <Text style={styles.videoPreviewCue}>No video available for this sign yet.</Text>
      </View>
    );
  }

  const html = `<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { background: #1F2924; width: 100%; height: 100%; overflow: hidden; }
    body { display: flex; justify-content: center; align-items: flex-start; }
    .signasldata-embed { width: 100%; border: none; }
  </style>
</head>
<body>
  <blockquote class="signasldata-embed" data-vidref="${vidref}"></blockquote>
  <script async src="https://embed.signasl.org/widgets.js" charset="utf-8"></script>
</body>
</html>`;

  if (Platform.OS === 'web') {
    return (
      <View style={{ width: 420, alignSelf: 'center', height: 270, overflow: 'hidden', borderRadius: 20 }}>
        {/* @ts-ignore */}
        <iframe srcDoc={html} style={{ width: 420, height: 520, border: 'none', display: 'block', marginTop: -110 }} />
      </View>
    );
  }

  return (
    <View style={styles.signAslClip}>
      <WebView
        source={{ html }}
        style={styles.signAslWebView}
        scrollEnabled={false}
        allowsInlineMediaPlayback
        mediaPlaybackRequiresUserAction={false}
        javaScriptEnabled
        originWhitelist={['*']}
      />
    </View>
  );
}

function PredictionCard({ result }: { result: VerifyResult }) {
  const alternatives = (result.candidates ?? []).filter(
    (candidate) => candidate.sign !== result.detected_sign
  );

  return (
    <View style={styles.predictionCard}>
      <Text style={styles.predictionEyebrow}>Model Prediction</Text>
      <Text style={styles.predictionSign}>
        {result.detected_sign || 'No sign detected'}
      </Text>
      <Text style={styles.predictionConfidence}>
        Confidence {result.confidence.toFixed(0)}%
      </Text>

      {alternatives.length > 0 ? (
        <View style={styles.alternativePredictions}>
          <Text style={styles.alternativeTitle}>Other guesses</Text>
          {alternatives.slice(0, 2).map((candidate) => (
            <View
              key={`${candidate.sign}-${candidate.class_index ?? candidate.model_label ?? 'candidate'}`}
              style={styles.alternativeRow}
            >
              <Text style={styles.alternativeSign}>{candidate.sign}</Text>
              <Text style={styles.alternativeScore}>{candidate.score.toFixed(0)}%</Text>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function ScoresCard({ attempt }: { attempt: any }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Scores</Text>
      {attempt.accuracy_score != null && (
        <ScoreRow label="Accuracy" value={attempt.accuracy_score} />
      )}
      {attempt.speed_score != null && (
        <ScoreRow label="Speed" value={attempt.speed_score} />
      )}
      {attempt.handshape_score != null && (
        <ScoreRow label="Handshape" value={attempt.handshape_score} />
      )}
      {attempt.score != null && (
        <ScoreRow label="Overall" value={attempt.score} bold />
      )}
    </View>
  );
}

function ScoreRow({ label, value, bold }: { label: string; value: number; bold?: boolean }) {
  return (
    <View style={styles.scoreRow}>
      <Text style={[styles.scoreLabel, bold && styles.scoreLabelBold]}>{label}</Text>
      <Text style={[styles.scoreValue, bold && styles.scoreValueBold]}>
        {value.toFixed(1)}%
      </Text>
    </View>
  );
}

function FeedbackCard({ attempt }: { attempt: any }) {
  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>Coach Feedback</Text>
      <Text style={styles.cardBody}>{attempt.coach_summary}</Text>
      {attempt.feedback_items?.map((item: string, i: number) => (
        <Text key={i} style={styles.feedbackItem}>• {item}</Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: palette.background },
  scroll: { padding: 16, gap: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: palette.background, padding: 24 },
  inlineBackButton: { marginBottom: 20 },

  title: { fontSize: 22, fontWeight: 'bold', color: palette.text, textAlign: 'center', marginBottom: 8 },
  loadingText: { marginTop: 12, fontSize: 16, color: palette.text },
  errorText: { fontSize: 16, color: palette.text, textAlign: 'center', marginBottom: 16 },
  hint: { fontSize: 14, color: palette.text, textAlign: 'center', marginTop: 4 },

  card: {
    backgroundColor: palette.surface,
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: { fontSize: 16, fontWeight: 'bold', color: palette.text, marginBottom: 12 },
  cardBody: { fontSize: 15, color: palette.text, lineHeight: 22 },
  prompt: { fontSize: 18, fontWeight: 'bold', color: palette.text, marginBottom: 6 },
  targetSign: { fontSize: 14, color: palette.text, marginTop: 8 },
  targetSignValue: { fontWeight: 'bold', color: palette.text },

  // Camera
  cameraWrapper: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#000',
  },
  cameraWrapperWeb: {
    width: '100%',
    maxWidth: 400,
    aspectRatio: 3 / 4,
    alignSelf: 'center',
  },
  camera: { flex: 1 },
  recordingBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.55)',
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 5,
    gap: 6,
  },
  recordingDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#E55' },
  recordingText: { color: '#FFF', fontSize: 13, fontWeight: '600' },
  uploadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.65)',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  uploadingText: { color: palette.background, fontSize: 16, fontWeight: '600' },

  // Record / stop buttons
  recordBtn: {
    alignSelf: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: palette.text,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
  },
  recordBtnInner: { width: 36, height: 36, borderRadius: 18, backgroundColor: palette.background },
  photoBtnInner: { width: 36, height: 36, borderRadius: 4, backgroundColor: palette.background },
  stopBtn: {
    alignSelf: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: palette.text,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 4,
  },
  stopBtnInner: { width: 28, height: 28, borderRadius: 4, backgroundColor: palette.background },
  captureBtnDisabled: { opacity: 0.45 },

  // Results
  resultBanner: {
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  bannerPass: { backgroundColor: palette.accent },
  bannerFail: { backgroundColor: palette.text },
  resultIcon: { fontSize: 36, color: '#FFF', fontWeight: 'bold' },
  resultTitle: { fontSize: 20, fontWeight: 'bold', color: '#FFF' },
  resultSub: { fontSize: 14, color: 'rgba(255,255,255,0.85)', marginTop: 2 },
  predictionCard: {
    backgroundColor: '#6D7A71',
    borderRadius: 16,
    padding: 18,
    gap: 6,
  },
  predictionEyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: 'rgba(239,234,221,0.75)',
  },
  predictionSign: { fontSize: 28, fontWeight: 'bold', color: '#EFEADD' },
  predictionConfidence: { fontSize: 15, color: '#EFEADD' },
  warningCard: {
    backgroundColor: '#F4E2B8',
    borderRadius: 12,
    padding: 14,
    gap: 6,
  },
  warningTitle: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    color: '#5A4020',
  },
  warningText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#5A4020',
  },
  captureNoticeCard: {
    backgroundColor: '#E7EEF6',
    borderRadius: 12,
    padding: 14,
    gap: 10,
  },
  captureNoticeTitle: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    color: '#2E4057',
  },
  captureNoticePreview: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 10,
    backgroundColor: '#C9D4E1',
  },
  captureNoticeText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#2E4057',
  },
  alternativePredictions: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(239,234,221,0.2)',
    gap: 8,
  },
  alternativeTitle: { fontSize: 13, fontWeight: '700', color: 'rgba(239,234,221,0.8)' },
  alternativeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  alternativeSign: { fontSize: 15, color: '#EFEADD' },
  alternativeScore: { fontSize: 15, fontWeight: '700', color: '#EFEADD' },

  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: palette.background,
  },
  scoreLabel: { fontSize: 14, color: palette.text },
  scoreLabelBold: { fontWeight: 'bold' },
  scoreValue: { fontSize: 14, color: palette.text, fontWeight: '600' },
  scoreValueBold: { color: palette.text, fontWeight: 'bold' },

  feedbackList: { marginTop: 10, gap: 4 },
  feedbackItem: { fontSize: 14, color: palette.text, lineHeight: 20 },

  // Quiz mode
  videoPreviewCard: {
    backgroundColor: '#1F2924',
    borderRadius: 20,
    padding: 18,
    gap: 12,
  },
  signAslClip: {
    borderRadius: 20,
    overflow: 'hidden',
    height: 268,
    backgroundColor: '#000',
  },
  signAslWebView: {
    width: '100%',
    height: 520,
    marginTop: -110,
    backgroundColor: '#000',
  },
  videoPreviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  videoPreviewEyebrow: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    color: 'rgba(239,234,221,0.72)',
  },
  videoPreviewLoop: {
    fontSize: 12,
    fontWeight: '600',
    color: '#EFEADD',
  },
  videoPreviewCue: {
    fontSize: 15,
    color: '#EFEADD',
    lineHeight: 22,
  },
  videoStage: {
    width: '100%',
    aspectRatio: 16 / 9,
    borderRadius: 16,
    backgroundColor: '#121814',
    borderWidth: 1,
    borderColor: 'rgba(239,234,221,0.12)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  videoGuideHorizontal: {
    position: 'absolute',
    left: 18,
    right: 18,
    height: 1,
    backgroundColor: 'rgba(239,234,221,0.08)',
  },
  videoGuideVertical: {
    position: 'absolute',
    top: 18,
    bottom: 18,
    width: 1,
    backgroundColor: 'rgba(239,234,221,0.08)',
  },
  demoHand: {
    width: 44,
    height: 56,
    borderRadius: 18,
    backgroundColor: '#D9CBB3',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 4,
  },
  demoHandCore: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: 'rgba(60,67,61,0.22)',
  },
  videoProgressTrack: {
    height: 6,
    borderRadius: 999,
    backgroundColor: 'rgba(239,234,221,0.12)',
    overflow: 'hidden',
  },
  videoProgressFill: {
    height: '100%',
    borderRadius: 999,
    backgroundColor: '#C9B89C',
  },
  videoStepText: {
    fontSize: 14,
    color: '#EFEADD',
    fontWeight: '600',
    textAlign: 'center',
  },
  quizInput: {
    backgroundColor: palette.surface,
    borderWidth: 1.5,
    borderColor: palette.accent,
    padding: 15,
    borderRadius: 12,
    fontSize: 16,
    color: palette.text,
  },

  resultActions: { flexDirection: 'row', gap: 12 },
  retryBtn: {
    flex: 1,
    borderWidth: 2,
    borderColor: palette.text,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  retryBtnText: { color: palette.text, fontSize: 16, fontWeight: 'bold' },
  submitBtn: { flex: 1 },

  btn: {
    backgroundColor: palette.text,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  btnDisabled: { backgroundColor: palette.accent },
  btnText: { color: palette.background, fontSize: 16, fontWeight: 'bold' },
});
