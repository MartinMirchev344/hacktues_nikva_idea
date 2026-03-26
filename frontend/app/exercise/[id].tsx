import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../context/auth-context';
import { getAttemptDetail, submitAttempt } from '../../lib/auth-api';

export default function Exercise() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { auth } = useAuth();
  const [attempt, setAttempt] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const handleCompleteExercise = async () => {
    if (!auth || !attempt) return;

    setIsSubmitting(true);
    try {
      // Placeholder: submit dummy data
      // In real app, this would be actual tracking data and scores
      await submitAttempt(attempt.id, {
        accuracy_score: 85,
        speed_score: 90,
        handshape_score: 80,
        detected_sign: 'example_sign',
        tracking_data: { placeholder: true },
      });
      Alert.alert('Success', 'Exercise completed! You earned 20 XP.', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to submit exercise');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!auth) {
    return (
      <View style={styles.center}>
        <Text>Please log in to practice exercises.</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#BA806A" />
        <Text style={styles.loadingText}>Loading exercise...</Text>
      </View>
    );
  }

  if (error || !attempt) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || 'Exercise not found'}</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Exercise Practice</Text>
        <Text style={styles.status}>Status: {attempt.status}</Text>
      </View>

      <View style={styles.exerciseCard}>
        <Text style={styles.prompt}>
          {attempt.exercise?.prompt || 'Practice this gesture'}
        </Text>
        <Text style={styles.instructions}>
          {attempt.exercise?.instructions || 'Follow the guide to perform the sign correctly.'}
        </Text>
        <Text style={styles.exerciseType}>
          Type: {attempt.exercise?.exercise_type.replace(/_/g, ' ') || 'Unknown'}
        </Text>
        <Text style={styles.target}>
          Target: {attempt.exercise?.expected_sign || 'Sign'}
        </Text>
        <Text style={styles.repetitions}>
          Repetitions: {attempt.exercise?.repetitions_target || 5}
        </Text>
      </View>

      {attempt.accuracy_score !== null && (
        <View style={styles.scoresCard}>
          <Text style={styles.scoresTitle}>Scores</Text>
          <View style={styles.scoreRow}>
            <Text style={styles.scoreLabel}>Accuracy:</Text>
            <Text style={styles.scoreValue}>{attempt.accuracy_score.toFixed(1)}%</Text>
          </View>
          {attempt.speed_score !== null && (
            <View style={styles.scoreRow}>
              <Text style={styles.scoreLabel}>Speed:</Text>
              <Text style={styles.scoreValue}>{attempt.speed_score.toFixed(1)}%</Text>
            </View>
          )}
          {attempt.handshape_score !== null && (
            <View style={styles.scoreRow}>
              <Text style={styles.scoreLabel}>Handshape:</Text>
              <Text style={styles.scoreValue}>{attempt.handshape_score.toFixed(1)}%</Text>
            </View>
          )}
          {attempt.score !== null && (
            <View style={styles.scoreRow}>
              <Text style={[styles.scoreLabel, styles.overallScore]}>Overall:</Text>
              <Text style={[styles.scoreValue, styles.overallScore]}>
                {attempt.score.toFixed(1)}%
              </Text>
            </View>
          )}
        </View>
      )}

      {attempt.status === 'in_progress' && (
        <View style={styles.trackingArea}>
          <Text style={styles.trackingTitle}>Hand Tracking Area</Text>
          <View style={styles.cameraPlaceholder}>
            <Text style={styles.placeholderText}>
              Camera and hand-tracking integration coming soon!
            </Text>
            <Text style={styles.placeholderText}>
              This area will show live camera feed and pose detection.
            </Text>
          </View>
        </View>
      )}

      {attempt.coach_summary && (
        <View style={styles.feedbackCard}>
          <Text style={styles.feedbackTitle}>Coach Summary</Text>
          <Text style={styles.feedbackText}>{attempt.coach_summary}</Text>
        </View>
      )}

      {attempt.status === 'in_progress' && (
        <TouchableOpacity
          style={[styles.completeButton, isSubmitting && styles.disabledButton]}
          onPress={handleCompleteExercise}
          disabled={isSubmitting}
        >
          <Text style={styles.completeButtonText}>
            {isSubmitting ? 'Submitting...' : 'Complete Exercise'}
          </Text>
        </TouchableOpacity>
      )}

      {attempt.status !== 'in_progress' && (
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Text style={styles.backText}>Back to Lesson</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#EFEADD',
    padding: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#EFEADD',
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#6D7A71',
    textAlign: 'center',
  },
  status: {
    fontSize: 16,
    color: '#BA806A',
    textAlign: 'center',
    textTransform: 'capitalize',
  },
  exerciseCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  prompt: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 8,
  },
  instructions: {
    fontSize: 16,
    color: '#6D7A71',
    marginBottom: 8,
  },
  exerciseType: {
    fontSize: 14,
    color: '#BA806A',
    marginBottom: 8,
    textTransform: 'capitalize',
  },
  target: {
    fontSize: 14,
    color: '#6D7A71',
    marginBottom: 8,
  },
  repetitions: {
    fontSize: 14,
    color: '#6D7A71',
  },
  scoresCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  scoresTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 12,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#EFEADD',
  },
  scoreLabel: {
    fontSize: 14,
    color: '#6D7A71',
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#BA806A',
  },
  overallScore: {
    fontWeight: 'bold',
    color: '#6D7A71',
  },
  trackingArea: {
    flex: 1,
    marginBottom: 16,
  },
  trackingTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 8,
    textAlign: 'center',
  },
  cameraPlaceholder: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  placeholderText: {
    fontSize: 16,
    color: '#6D7A71',
    textAlign: 'center',
    marginBottom: 8,
  },
  feedbackCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  feedbackTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 8,
  },
  feedbackText: {
    fontSize: 14,
    color: '#6D7A71',
    lineHeight: 20,
  },
  completeButton: {
    backgroundColor: '#BA806A',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  disabledButton: {
    backgroundColor: '#CCCCCC',
  },
  completeButtonText: {
    color: '#EFEADD',
    fontSize: 18,
    fontWeight: 'bold',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6D7A71',
  },
  errorText: {
    fontSize: 16,
    color: '#BA806A',
    textAlign: 'center',
    marginBottom: 16,
  },
  backButton: {
    backgroundColor: '#BA806A',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  backText: {
    color: '#EFEADD',
    fontSize: 16,
    fontWeight: 'bold',
  },
});