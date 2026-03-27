import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Redirect, useRouter, useLocalSearchParams, useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../context/auth-context';
import { getLesson, createAttempt, getMyAttempts, Lesson, Exercise } from '../../lib/auth-api';
import { palette } from '../../constants/colors';
import { ScreenBackButton } from '../../components/screen-back-button';

function shuffleExercises(exercises: Exercise[]) {
  const shuffled = [...exercises];

  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }

  return shuffled;
}

function buildMixedExerciseOrder(exercises: Exercise[]) {
  const ordered = [...exercises].sort((a, b) => a.order - b.order);
  const practiceExercises = ordered.filter((exercise) => exercise.exercise_type !== 'quiz');
  const quizExercises = shuffleExercises(
    ordered.filter((exercise) => exercise.exercise_type === 'quiz')
  );

  if (practiceExercises.length > 0 && quizExercises.length > 1) {
    const lastPracticeSign = practiceExercises[practiceExercises.length - 1].expected_sign;

    if (quizExercises[0].expected_sign === lastPracticeSign) {
      const swapIndex = quizExercises.findIndex(
        (exercise, index) => index > 0 && exercise.expected_sign !== lastPracticeSign
      );

      if (swapIndex !== -1) {
        [quizExercises[0], quizExercises[swapIndex]] = [quizExercises[swapIndex], quizExercises[0]];
      }
    }
  }

  return [...practiceExercises, ...quizExercises];
}

export default function LessonDetail() {
  const router = useRouter();
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { auth, isHydrating } = useAuth();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [completedExerciseIds, setCompletedExerciseIds] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      if (!auth || !slug) return;

      const fetchLesson = async () => {
        try {
          setLoading(true);
          const [lesson, attempts] = await Promise.all([getLesson(slug), getMyAttempts()]);
          setLesson(lesson);
          const exs = buildMixedExerciseOrder(lesson.exercises || []);
          setExercises(exs);
          const exerciseIds = new Set(exs.map(e => e.id));
          const completed = new Set(
            attempts
              .filter(a =>
                exerciseIds.has(a.exercise.id) &&
                a.status === 'completed' &&
                (a.score ?? a.accuracy_score ?? 0) >= (a.exercise.passing_score ?? 70)
              )
              .map(a => a.exercise.id)
          );
          setCompletedExerciseIds(completed);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load lesson');
        } finally {
          setLoading(false);
        }
      };

      fetchLesson();
    }, [auth, slug])
  );

  const handleStartExercise = async (exercise: Exercise) => {
    if (!auth) return;
    try {
      const attempt = await createAttempt(exercise.id);
      const maxOrder = Math.max(...exercises.map(e => e.order));
      const isLast = exercise.order === maxOrder;
      router.push({ pathname: `/exercise/${attempt.id}`, params: { isLastExercise: isLast ? '1' : '0' } });
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to start exercise');
    }
  };

  const handleStartLesson = async () => {
    if (!auth || exercises.length === 0) return;
    try {
      const attempt = await createAttempt(exercises[0].id);
      const queue = JSON.stringify(exercises.map(e => e.id));
      router.push({ pathname: `/exercise/${attempt.id}`, params: { exerciseQueue: queue, queueIndex: '0' } });
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to start lesson');
    }
  };

  const exerciseTypeLabel = (type: string) => {
    if (type === 'quiz') return 'Watch & Guess';
    if (type === 'gesture_practice' || type === 'movement_drill') return 'Practice Signs';
    return type.replace(/_/g, ' ');
  };

  const renderExercise = ({ item }: { item: Exercise }) => {
    const done = completedExerciseIds.has(item.id);
    const isQuiz = item.exercise_type === 'quiz';
    return (
      <View style={[styles.exerciseCard, done && styles.exerciseCardDone]}>
        <View style={styles.exerciseHeader}>
          <Text style={styles.exercisePrompt}>
            {item.prompt}
          </Text>
          {done && <Text style={styles.doneBadge}>✓ Done</Text>}
        </View>
        <Text style={styles.exerciseInstructions}>
          {item.instructions}
        </Text>
        <Text style={styles.exerciseType}>{exerciseTypeLabel(item.exercise_type)}</Text>
        <TouchableOpacity
          style={[styles.startButton, done && styles.retakeButton]}
          onPress={() => handleStartExercise(item)}
        >
          <Text style={[styles.startButtonText, done && styles.retakeButtonText]}>{done ? 'Retake' : 'Start Exercise'}</Text>
        </TouchableOpacity>
      </View>
    );
  };

  if (isHydrating) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={palette.text} />
        <Text style={styles.loadingText}>Loading lesson...</Text>
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
        <Text style={styles.loadingText}>Loading lesson...</Text>
      </View>
    );
  }

  if (error || !lesson) {
    return (
      <View style={styles.center}>
        <ScreenBackButton fallbackHref="/home" style={styles.centerBackButton} />
        <Text style={styles.errorText}>{error || 'Lesson not found'}</Text>
      </View>
    );
  }

  return (
    <SafeAreaView edges={['top']} style={styles.safeArea}>
    <View style={styles.container}>
      <View style={styles.topBar}>
        <ScreenBackButton fallbackHref="/home" />
      </View>
      <View style={styles.header}>
        <Text style={styles.title}>{lesson.title}</Text>
        <Text style={styles.description}>{lesson.description}</Text>
        <View style={styles.meta}>
          <Text style={styles.difficulty}>{lesson.difficulty}</Text>
          <Text style={styles.duration}>{lesson.estimated_duration_minutes} minutes</Text>
        </View>
        <Text style={styles.challengeNote}>Practice comes first, then the guessing exercises are mixed up.</Text>
        <TouchableOpacity style={styles.startLessonButton} onPress={handleStartLesson}>
          <Text style={styles.startLessonText}>Start Lesson</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.exercisesTitle}>Exercises ({exercises.length})</Text>

      <FlatList
        data={exercises}
        renderItem={renderExercise}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: palette.background,
  },
  container: {
    flex: 1,
    padding: 16,
  },
  topBar: {
    marginBottom: 16,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.background,
  },
  header: {
    backgroundColor: palette.surface,
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: palette.text,
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: palette.text,
    marginBottom: 12,
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  difficulty: {
    fontSize: 14,
    color: palette.text,
    textTransform: 'capitalize',
    fontWeight: '600',
    opacity: 0.75,
  },
  duration: {
    fontSize: 14,
    color: palette.text,
  },
  challengeNote: {
    fontSize: 13,
    color: palette.text,
    opacity: 0.75,
    marginTop: 10,
  },
  startLessonButton: {
    backgroundColor: palette.text,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 14,
  },
  startLessonText: {
    color: palette.background,
    fontSize: 17,
    fontWeight: 'bold',
  },
  exercisesTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: palette.text,
    marginBottom: 12,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: palette.text,
  },
  errorText: {
    fontSize: 16,
    color: palette.text,
    textAlign: 'center',
    marginBottom: 16,
  },
  centerBackButton: {
    marginBottom: 20,
  },
  list: {
    paddingBottom: 20,
  },
  exerciseCard: {
    backgroundColor: palette.surface,
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  exerciseCardDone: {
    opacity: 0.75,
    borderLeftWidth: 4,
    borderLeftColor: palette.accent,
  },
  exerciseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  exercisePrompt: {
    fontSize: 16,
    fontWeight: 'bold',
    color: palette.text,
    flex: 1,
  },
  doneBadge: {
    fontSize: 13,
    fontWeight: '700',
    color: palette.accent,
    marginLeft: 8,
  },
  exerciseInstructions: {
    fontSize: 14,
    color: palette.text,
    marginBottom: 10,
  },
  exerciseType: {
    fontSize: 12,
    color: palette.text,
    textTransform: 'capitalize',
    opacity: 0.75,
    marginBottom: 12,
  },
  startButton: {
    backgroundColor: palette.text,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  retakeButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: palette.text,
  },
  startButtonText: {
    color: palette.background,
    fontSize: 16,
    fontWeight: 'bold',
  },
  retakeButtonText: {
    color: palette.text,
  },
});
