import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useAuth } from '../../context/auth-context';
import { getLesson, createAttempt, Lesson, Exercise } from '../../lib/auth-api';

export default function LessonDetail() {
  const router = useRouter();
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const { auth } = useAuth();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auth || !slug) return;

    const fetchLesson = async () => {
      try {
        setLoading(true);
        const lesson = await getLesson(slug);
        setLesson(lesson);
        setExercises(lesson.exercises || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lesson');
      } finally {
        setLoading(false);
      }
    };

    fetchLesson();
  }, [auth, slug]);

  const handleStartExercise = async (exercise: Exercise) => {
    if (!auth) return;

    try {
      const attempt = await createAttempt(exercise.id);
      router.push(`/exercise/${attempt.id}`);
    } catch (err) {
      Alert.alert('Error', err instanceof Error ? err.message : 'Failed to start exercise');
    }
  };

  const renderExercise = ({ item }: { item: Exercise }) => (
    <View style={styles.exerciseCard}>
      <Text style={styles.exercisePrompt}>{item.prompt}</Text>
      <Text style={styles.exerciseInstructions}>{item.instructions}</Text>
      <View style={styles.exerciseMeta}>
        <Text style={styles.exerciseType}>{item.exercise_type.replace(/_/g, ' ')}</Text>
        <Text style={styles.repetitions}>Target: {item.repetitions_target}</Text>
      </View>
      <TouchableOpacity
        style={styles.startButton}
        onPress={() => handleStartExercise(item)}
      >
        <Text style={styles.startButtonText}>Start Exercise</Text>
      </TouchableOpacity>
    </View>
  );

  if (!auth) {
    return (
      <View style={styles.center}>
        <Text>Please log in to view this lesson.</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#BA806A" />
        <Text style={styles.loadingText}>Loading lesson...</Text>
      </View>
    );
  }

  if (error || !lesson) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{error || 'Lesson not found'}</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Text style={styles.backText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>{lesson.title}</Text>
        <Text style={styles.description}>{lesson.description}</Text>
        <View style={styles.meta}>
          <Text style={styles.difficulty}>{lesson.difficulty}</Text>
          <Text style={styles.duration}>{lesson.estimated_duration_minutes} minutes</Text>
        </View>
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
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 8,
  },
  description: {
    fontSize: 16,
    color: '#6D7A71',
    marginBottom: 12,
  },
  meta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  difficulty: {
    fontSize: 14,
    color: '#BA806A',
    textTransform: 'capitalize',
    fontWeight: '600',
  },
  duration: {
    fontSize: 14,
    color: '#6D7A71',
  },
  exercisesTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 12,
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
  },
  backText: {
    color: '#EFEADD',
    fontSize: 16,
    fontWeight: 'bold',
  },
  list: {
    paddingBottom: 20,
  },
  exerciseCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  exercisePrompt: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 8,
  },
  exerciseInstructions: {
    fontSize: 14,
    color: '#6D7A71',
    marginBottom: 12,
  },
  exerciseMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  exerciseType: {
    fontSize: 12,
    color: '#BA806A',
    textTransform: 'capitalize',
  },
  repetitions: {
    fontSize: 12,
    color: '#6D7A71',
  },
  startButton: {
    backgroundColor: '#BA806A',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  startButtonText: {
    color: '#EFEADD',
    fontSize: 16,
    fontWeight: 'bold',
  },
});