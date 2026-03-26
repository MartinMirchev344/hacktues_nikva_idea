import { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Image,
  Dimensions,
  StyleSheet,
} from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { useAuth } from '../context/auth-context';
import { getLessons, Lesson } from '../lib/auth-api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

const POSITIONS = [
  SCREEN_WIDTH * 0.05,
  SCREEN_WIDTH * 0.45,
  SCREEN_WIDTH * 0.15,
  SCREEN_WIDTH * 0.50,
  SCREEN_WIDTH * 0.08,
  SCREEN_WIDTH * 0.42,
  SCREEN_WIDTH * 0.20,
  SCREEN_WIDTH * 0.48,
  SCREEN_WIDTH * 0.05,
  SCREEN_WIDTH * 0.40,
];

const CLOUD_WIDTH = SCREEN_WIDTH * 0.48;
const CLOUD_HEIGHT = 80;
const VERTICAL_SPACING = 130;

function CloudShape({ width = CLOUD_WIDTH, height = CLOUD_HEIGHT, color = '#FFFFFF' }: { width?: number; height?: number; color?: string }) {
  const bumpSize = height * 0.75;
  return (
    <View style={{ width, height, position: 'relative' }}>
      <View style={{
        position: 'absolute',
        width: bumpSize * 0.85,
        height: bumpSize * 0.85,
        borderRadius: bumpSize,
        backgroundColor: color,
        bottom: height * 0.28,
        left: width * 0.08,
      }} />
      <View style={{
        position: 'absolute',
        width: bumpSize,
        height: bumpSize,
        borderRadius: bumpSize,
        backgroundColor: color,
        bottom: height * 0.32,
        left: width * 0.28,
      }} />
      <View style={{
        position: 'absolute',
        width: bumpSize * 0.7,
        height: bumpSize * 0.7,
        borderRadius: bumpSize,
        backgroundColor: color,
        bottom: height * 0.24,
        left: width * 0.56,
      }} />
      <View style={{
        position: 'absolute',
        width,
        height: height * 0.55,
        borderRadius: height * 0.3,
        backgroundColor: color,
        bottom: 0,
      }} />
    </View>
  );
}

export default function Home() {
  const router = useRouter();
  const { auth, logout } = useAuth();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auth) return;
    const load = async () => {
      try {
        setLoading(true);
        setLessons(await getLessons());
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load lessons');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [auth]);

  if (!auth) return <Redirect href="/signup" />;

  const currentLessonIndex = 0;
  const totalHeight = lessons.length * VERTICAL_SPACING + 200;

  return (
    <View style={styles.container}>
      <View style={[StyleSheet.absoluteFillObject, { backgroundColor: '#1a6fad' }]} />
      <View style={[StyleSheet.absoluteFillObject, { backgroundColor: '#3a8fcc', top: '20%' }]} />
      <View style={[StyleSheet.absoluteFillObject, { backgroundColor: '#5aaee0', top: '45%' }]} />
      <View style={[StyleSheet.absoluteFillObject, { backgroundColor: '#7ec8f0', top: '65%' }]} />
      <View style={[StyleSheet.absoluteFillObject, { backgroundColor: '#a8ddf5', top: '80%' }]} />

      <View style={styles.header}>
        <Text style={styles.xpText}>⭐ {auth.user.xp} XP</Text>
        <Text style={styles.streakText}>🔥 {auth.user.streak} day streak</Text>
        <TouchableOpacity onPress={() => { logout(); router.replace('/'); }}>
          <Text style={styles.logoutText}>Log out</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color="#fff" style={{ marginTop: 60 }} />
      ) : error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : (
        <ScrollView
          contentContainerStyle={{ height: totalHeight, position: 'relative' }}
          showsVerticalScrollIndicator={false}
        >
          {lessons.map((lesson, index) => {
            const left = POSITIONS[index % POSITIONS.length];
            const top = index * VERTICAL_SPACING + 20;
            const isCurrent = index === currentLessonIndex;

            return (
              <View key={lesson.id} style={{ position: 'absolute', left, top }}>
                {isCurrent && (
                  <Image
                    source={require('../assets/beaver.png')}
                    style={styles.beaver}
                    resizeMode="contain"
                  />
                )}
                <TouchableOpacity
                  onPress={() => router.push(`/lessons/${lesson.slug}`)}
                  activeOpacity={0.85}
                >
                  <CloudShape color={isCurrent ? '#FFE97A' : '#FFFFFF'} />
                  <View style={styles.cloudLabel}>
                    <Text style={styles.cloudTitle} numberOfLines={1}>{lesson.title}</Text>
                    <Text style={styles.cloudMeta}>
                      {lesson.difficulty} • {(lesson as any).exercise_count ?? 0} exercises
                    </Text>
                  </View>
                </TouchableOpacity>
              </View>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 52,
    paddingBottom: 12,
    zIndex: 10,
  },
  xpText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  streakText: { color: '#FFE97A', fontWeight: 'bold', fontSize: 15 },
  logoutText: { color: '#ffffff99', fontSize: 13 },
  beaver: {
    width: 70,
    height: 70,
    position: 'absolute',
    top: -65,
    left: CLOUD_WIDTH * 0.3,
    zIndex: 10,
  },
  cloudLabel: {
    position: 'absolute',
    bottom: 10,
    left: 0,
    width: CLOUD_WIDTH,
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  cloudTitle: { fontWeight: 'bold', fontSize: 14, color: '#3a5a6a', textAlign: 'center' },
  cloudMeta: { fontSize: 11, color: '#5a7a8a', textAlign: 'center' },
  errorText: { color: '#fff', textAlign: 'center', marginTop: 40 },
});
