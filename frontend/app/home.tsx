import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  Image,
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
  const floatAnim = useRef(new Animated.Value(0)).current;

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

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: 1,
          duration: 3200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 3200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    ).start();
  }, [floatAnim]);

  if (!auth) {
    return <Redirect href="/signup" />;
  }

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  const skyClouds = [
    { top: 60, left: 14, width: 100, height: 58, opacity: 0.7 },
    { top: 26, right: 24, width: 130, height: 64, opacity: 0.8 },
    { top: 170, left: 8, width: 86, height: 48, opacity: 0.73 },
    { top: 242, right: 12, width: 118, height: 62, opacity: 0.78 },
    { top: 318, left: 52, width: 124, height: 66, opacity: 0.72 },
    { top: 130, right: 90, width: 70, height: 40, opacity: 0.6 },
    { top: 240, left: 10, width: 80, height: 46, opacity: 0.65 },
  ];

  const beaverImg = require('../assets/beaver.png');

  const renderLesson = ({ item, index }: { item: Lesson; index: number }) => {
    const exerciseCount = item['exercise_count'] ?? item.exercises?.length ?? 0;
    const floatY = floatAnim.interpolate({
      inputRange: [0, 1],
      outputRange: [0, index % 2 === 0 ? -6 : 6],
    });
    const floatX = floatAnim.interpolate({
      inputRange: [0, 1],
      outputRange: [index % 2 === 0 ? -4 : 4, index % 2 === 0 ? 4 : -4],
    });

    return (
      <Animated.View
        style={[
          styles.lessonWrapper,
          {
            transform: [{ translateY: floatY }, { translateX: floatX }],
          },
        ]}
      >
        <TouchableOpacity
          style={styles.lessonCloud}
          onPress={() => router.push(`/lessons/${item.slug}`)}
          activeOpacity={0.9}
        >
          <Text style={styles.lessonTitleCloud}>{item.title}</Text>
          <Text style={styles.lessonMetaCloud}>
            Difficulty: {item.difficulty} • {exerciseCount} exercises
          </Text>
          {index === 1 && (
            <Image source={beaverImg} style={styles.beaver} resizeMode='contain' />
          )}
        </TouchableOpacity>
      </Animated.View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.skyTopGradient} />
      <View style={styles.skyBottomGradient} />
      {skyClouds.map((c, i) => (
        <View key={`decor-${i}`} style={[styles.skyCloud, c]} />
      ))}

      <View style={styles.headerRow}>
        <View style={styles.xpBubble}>
          <Text style={styles.xpNumber}>{auth.user.xp}</Text>
          <Text style={styles.xpLabel}>XP</Text>
        </View>
        <View style={styles.streakBubble}>
          <Text style={styles.streakNumber}>{auth.user.streak}</Text>
          <Text style={styles.streakLabel}>streak</Text>
        </View>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.welcomeSection}>
        <Text style={styles.welcome}>Welcome, {auth.user.username}</Text>
        <Text style={styles.subtitle}>Choose a lesson to start practicing</Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color="#BA806A" style={{ marginTop: 20 }} />
      ) : error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : lessons.length === 0 ? (
        <Text style={styles.emptyText}>No lessons are available right now. Please check back soon.</Text>
      ) : (
        <FlatList
          data={lessons}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderLesson}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 40,
    backgroundColor: '#6EA8E6',
  },
  welcome: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#BA806A',
    marginBottom: 12,
    textAlign: 'center',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    paddingHorizontal: 16,
  },
  xpBubble: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    paddingVertical: 6,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 3,
  },
  xpNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6EA8E6',
  },
  xpLabel: {
    fontSize: 10,
    color: '#6D7A71',
  },
  logoutButton: {
    backgroundColor: '#BA806A',
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 3,
  },
  logoutText: {
    color: '#EFEADD',
    fontSize: 14,
    fontWeight: 'bold',
  },
  welcomeSection: {
    alignItems: 'center',
    marginBottom: 40,
  },
  meta: {
    fontSize: 14,
    color: '#6D7A71',
    marginBottom: 16,
  },
  streakBubble: {
    backgroundColor: '#ffffff',
    borderRadius: 24,
    paddingVertical: 6,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
    elevation: 3,
  },
  streakNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#6EA8E6',
  },
  streakLabel: {
    fontSize: 10,
    color: '#6D7A71',
  },
  list: {
    paddingBottom: 20,
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
  lessonWrapper: {
    marginBottom: 18,
    alignItems: 'center',
  },
  skyTopGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    top: 0,
    height: 200,
    backgroundColor: '#73c2fb',
    opacity: 0.95,
  },
  skyBottomGradient: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 220,
    backgroundColor: '#98d8ff',
    opacity: 0.92,
  },
  skyCloud: {
    position: 'absolute',
    backgroundColor: '#ffffff',
    borderRadius: 200,
    opacity: 0.2,
  },
  lessonCloud: {
    width: '88%',
    minHeight: 120,
    backgroundColor: '#ffffff',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 5,
    borderWidth: 2,
    borderColor: '#E8F4FD',
  },
  cloudImage: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: 40,
  },
  lessonTitleCloud: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#093A65',
    zIndex: 2,
    marginTop: 12,
    textAlign: 'center',
  },
  lessonMetaCloud: {
    fontSize: 12,
    color: '#1A4E9D',
    zIndex: 2,
    marginTop: 8,
    textAlign: 'center',
  },
  beaver: {
    position: 'absolute',
    width: 70,
    height: 70,
    right: 10,
    top: 10,
    zIndex: 3,
  },
  // legacy cloud-shape styles are removed; images are now used instead.
  cloudBase: {
    position: 'absolute',
    bottom: 8,
    width: '100%',
    height: 62,
    backgroundColor: '#fff',
    borderRadius: 32,
  },
  cloudBump: {
    position: 'absolute',
    top: 0,
    width: 80,
    height: 80,
    backgroundColor: '#fff',
    borderRadius: 40,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  lessonCard: {
    width: '100%',
    backgroundColor: 'transparent',
    padding: 16,
    zIndex: 1,
  },
  errorText: {
    color: '#BA806A',
    textAlign: 'center',
    marginTop: 16,
  },
  emptyText: {
    color: '#ffffff',
    textAlign: 'center',
    marginTop: 20,
    fontSize: 16,
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