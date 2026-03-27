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
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Audio } from 'expo-av';
import { Redirect, useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../context/auth-context';
import {
  getAttemptDetail,
  createAttempt,
  submitAttempt,
  verifySign,
  getMyAttempts,
  VerifyResult,
} from '../../lib/auth-api';
import { palette } from '../../constants/colors';
import { ScreenBackButton } from '../../components/screen-back-button';

type Phase = 'idle' | 'recording' | 'uploading' | 'results';
type QuizPhase = 'answering' | 'results';

export default function Exercise() {
  const router = useRouter();
  const { id, isLastExercise, exerciseQueue, queueIndex } = useLocalSearchParams<{
    id: string;
    isLastExercise?: string;
    exerciseQueue?: string;
    queueIndex?: string;
  }>();
  const { auth, isHydrating } = useAuth();

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

  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView | null>(null);

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
    cameraRef.current?.stopRecording();
  };

  const retryRecording = () => {
    setResult(null);
    setPhase('idle');
  };

  const handleSubmit = async () => {
    if (!result) return;
    setIsSubmitting(true);
    try {
      await submitAttempt(attempt.id, {
        status: 'completed',
        accuracy_score: result.accuracy_score,
        speed_score: result.speed_score,
        handshape_score: result.handshape_score,
        detected_sign: result.detected_sign,
        coach_summary: result.coach_summary,
        feedback_items: result.feedback_items,
        completed_at: new Date().toISOString(),
      });
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
      quizAnswer.trim().toLowerCase() ===
      attempt.exercise?.expected_sign?.toLowerCase();
    setQuizCorrect(correct);
    setQuizPhase('results');
    playSound(correct ? 'correct' : 'fail');
  };

  const handleQuizSave = async () => {
    setIsSubmitting(true);
    try {
      await submitAttempt(attempt.id, {
        status: 'completed',
        accuracy_score: quizCorrect ? 100 : 0,
        detected_sign: quizAnswer.trim(),
        completed_at: new Date().toISOString(),
      });
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
  if (permission && !permission.granted) {
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

  const isQuiz = attempt.exercise?.exercise_type === 'quiz';

  if (isQuiz) {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scroll} bounces={false}>
          <ScreenBackButton fallbackHref="/home" />
          <ExerciseCard attempt={attempt} />

          {/* Gesture video placeholder */}
          <View style={styles.videoPlaceholder}>
            <Text style={styles.videoPlaceholderIcon}>▶</Text>
            <Text style={styles.videoPlaceholderText}>Gesture video coming soon</Text>
          </View>

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
                      Answer: {attempt.exercise?.expected_sign}
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

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} bounces={false}>
        <ScreenBackButton fallbackHref="/home" />
        {/* Exercise prompt */}
        <ExerciseCard attempt={attempt} />

        {/* Camera + controls */}
        {phase !== 'results' && (
          <View style={styles.cameraWrapper}>
            <CameraView
              ref={cameraRef}
              style={styles.camera}
              facing="front"
              mode="video"
            />

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
        {isQuiz ? 'Read the Sign' : (attempt.exercise?.prompt || 'Practice this sign')}
      </Text>
      <Text style={styles.cardBody}>
        {isQuiz
          ? 'Watch the gesture and type what phrase or word it represents.'
          : attempt.exercise?.instructions}
      </Text>
      {!isQuiz && (
        <Text style={styles.targetSign}>
          Sign: <Text style={styles.targetSignValue}>{attempt.exercise?.expected_sign}</Text>
        </Text>
      )}
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
  videoPlaceholder: {
    width: '100%',
    aspectRatio: 16 / 9,
    borderRadius: 16,
    backgroundColor: '#1a1a1a',
    borderWidth: 2,
    borderColor: palette.accent,
    borderStyle: 'dashed',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
  },
  videoPlaceholderIcon: { fontSize: 40, color: palette.accent },
  videoPlaceholderText: { fontSize: 15, color: palette.accent, fontWeight: '600' },
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
