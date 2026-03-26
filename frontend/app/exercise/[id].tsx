import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { CameraView, useCameraPermissions, CameraCapturedPicture } from 'expo-camera';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../context/auth-context';
import {
  getAttemptDetail,
  submitAttempt,
  verifySign,
  VerifyResult,
} from '../../lib/auth-api';
import { palette } from '../../constants/colors';

type Phase = 'idle' | 'recording' | 'uploading' | 'results';

export default function Exercise() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { auth } = useAuth();

  const [attempt, setAttempt] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>('idle');
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView | null>(null);

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
      router.back();
    } catch (err) {
      Alert.alert('Error', 'Failed to save results. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!auth) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Please log in to practice exercises.</Text>
      </View>
    );
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
        <Text style={styles.errorText}>{error || 'Exercise not found'}</Text>
        <TouchableOpacity style={styles.btn} onPress={() => router.back()}>
          <Text style={styles.btnText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Already completed
  if (attempt.status !== 'in_progress') {
    return (
      <SafeAreaView style={styles.container}>
        <ScrollView contentContainerStyle={styles.scroll}>
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
        <Text style={styles.errorText}>Camera access is required to practice signs.</Text>
        <TouchableOpacity style={styles.btn} onPress={requestPermission}>
          <Text style={styles.btnText}>Allow Camera</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} bounces={false}>
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
  return (
    <View style={styles.card}>
      <Text style={styles.prompt}>{attempt.exercise?.prompt || 'Practice this sign'}</Text>
      <Text style={styles.cardBody}>{attempt.exercise?.instructions}</Text>
      <Text style={styles.targetSign}>
        Sign: <Text style={styles.targetSignValue}>{attempt.exercise?.expected_sign}</Text>
      </Text>
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
