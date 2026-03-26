import { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { useAuth } from '../context/auth-context';
import { getLessons, Lesson } from '../lib/auth-api';

export default function Home() {
  const router = useRouter();
  const { auth, logout } = useAuth();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auth) {
      return;
    }

    const loadLessons = async () => {
      try {
        setLoading(true);
        const data = await getLessons();
        setLessons(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lessons');
      } finally {
        setLoading(false);
      }
    };

    loadLessons();
  }, [auth]);

  if (!auth) {
    return <Redirect href="/signup" />;
  }

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  const renderLesson = ({ item }: { item: Lesson }) => {
    const exerciseCount = item['exercise_count'] ?? item.exercises?.length ?? 0;
    return (
      <TouchableOpacity
        style={styles.lessonCard}
        onPress={() => router.push(`/lessons/${item.slug}`)}
      >
        <Text style={styles.lessonTitle}>{item.title}</Text>
        <Text style={styles.lessonDescription}>{item.description}</Text>
        <Text style={styles.lessonMeta}>
          Difficulty: {item.difficulty} • {exerciseCount} exercises
        </Text>
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.welcome}>Welcome, {auth.user.username}</Text>
      <Text style={styles.subtitle}>Choose a lesson to start practicing</Text>
      <Text style={styles.meta}>XP: {auth.user.xp} • Streak: {auth.user.streak}</Text>

      {loading ? (
        <ActivityIndicator size="large" color="#BA806A" style={{ marginTop: 20 }} />
      ) : error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : (
        <FlatList
          data={lessons}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderLesson}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}

      <TouchableOpacity style={styles.button} onPress={handleLogout}>
        <Text style={styles.buttonText}>Log Out</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 40,
    backgroundColor: '#EFEADD',
  },
  welcome: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#BA806A',
    marginBottom: 12,
    textAlign: 'center',
  },
  meta: {
    fontSize: 14,
    color: '#6D7A71',
    marginBottom: 16,
    textAlign: 'center',
  },
  list: {
    paddingBottom: 20,
  },
  lessonCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  lessonTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 6,
  },
  lessonDescription: {
    fontSize: 14,
    color: '#6D7A71',
    marginBottom: 8,
  },
  lessonMeta: {
    fontSize: 12,
    color: '#BA806A',
  },
  errorText: {
    color: '#BA806A',
    textAlign: 'center',
    marginTop: 16,
  },
  button: {
    marginTop: 12,
    backgroundColor: '#BA806A',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    alignSelf: 'center',
  },
  buttonText: {
    color: '#EFEADD',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
