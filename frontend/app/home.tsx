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
} from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { Redirect, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/auth-context';
import { getLessons, Lesson } from '../lib/auth-api';
import { palette } from '../constants/colors';

function streakColor(streak: number): string {
  if (streak <= 0) return '#AAAAAA';
  // Stops: orange → red → blue → purple
  const stops = ['#FF6600', '#CC0000', '#0055FF', '#7B00CC'];
  const total = stops.length - 1;
  const maxStreak = 30;
  const t = Math.min(streak / maxStreak, 1) * total;
  const i = Math.min(Math.floor(t), total - 1);
  const f = t - i;
  const hex = (h: string) => [
    parseInt(h.slice(1, 3), 16),
    parseInt(h.slice(3, 5), 16),
    parseInt(h.slice(5, 7), 16),
  ];
  const [r1, g1, b1] = hex(stops[i]);
  const [r2, g2, b2] = hex(stops[i + 1]);
  const r = Math.round(r1 + (r2 - r1) * f);
  const g = Math.round(g1 + (g2 - g1) * f);
  const b = Math.round(b1 + (b2 - b1) * f);
  return `rgb(${r},${g},${b})`;
}

function FlameIcon({ streak }: { streak: number }) {
  const color = streakColor(streak);
  return (
    <Svg width={38} height={46} viewBox="0 0 24 30">
      {/* Outer flame */}
      <Path
        d="M12 28 C6 25 2 20 2 14 C2 9 5 5 8 2 C8 6 10 8 12 9 C12 6 14 3 16 1 C18 5 22 9 22 14 C22 20 18 25 12 28 Z"
        fill={color}
        opacity={0.9}
      />
      {/* Inner highlight */}
      <Path
        d="M12 25 C9 22 8 18 9 14 C10 16 11 17 12 17 C13 15 13 12 14 10 C15 13 16 17 15 21 C14 23 13 24 12 25 Z"
        fill="rgba(255,255,255,0.35)"
      />
    </Svg>
  );
}

export default function Home() {
  const router = useRouter();
  const { auth, isHydrating, logout } = useAuth();
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

  if (isHydrating) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={palette.text} />
      </View>
    );
  }

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
          onPress={() =>
            router.push({
              pathname: '/lessons/[slug]',
              params: { slug: item.slug },
            })
          }
          activeOpacity={0.9}
        >
          <Text style={styles.lessonTitleCloud}>{item.title}</Text>
          <Text style={styles.lessonMetaCloud}>
            Difficulty: {item.difficulty} • {exerciseCount} exercises
          </Text>

        </TouchableOpacity>
      </Animated.View>
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.backgroundGlowTop} />
      <View style={styles.backgroundGlowBottom} />

      <View style={styles.heroPanel}>
        <View style={[styles.heroBlurOrb, styles.heroBlurOrbLarge]} />
        <View style={[styles.heroBlurOrb, styles.heroBlurOrbMedium]} />
        <View style={[styles.heroBlurOrb, styles.heroBlurOrbSmall]} />
        {skyClouds.map((c, i) => (
          <View key={`decor-${i}`} style={[styles.skyCloud, c]} />
        ))}

        <SafeAreaView edges={['top']} style={styles.heroSafeArea}>
          <View style={styles.headerRow}>
            <View style={styles.xpBubble}>
              <Text style={styles.xpNumber}>{auth.user.xp}</Text>
              <Text style={styles.xpLabel}>XP</Text>
            </View>
            <View style={styles.streakBubble}>
              <FlameIcon streak={auth.user.streak} />
              <Text style={[styles.streakNumber, { color: streakColor(auth.user.streak) }]}>
                {auth.user.streak}
              </Text>
            </View>
            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
              <Text style={styles.logoutText}>Log Out</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>

        <View style={styles.welcomeSection}>
          <TouchableOpacity style={styles.welcomeBadge} onPress={() => router.push('/alphabet')}>
            <Text style={styles.welcomeBadgeText}>ASL Alphabet</Text>
          </TouchableOpacity>
          <Text style={styles.welcome}>Welcome, {auth.user.username}</Text>
          <Text style={styles.subtitle}>Choose a lesson to start practicing</Text>
        </View>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={palette.text} style={{ marginTop: 20 }} />
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
    paddingHorizontal: 14,
    paddingTop: 10,
    backgroundColor: palette.background,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: palette.background,
  },
  welcome: {
    fontSize: 30,
    fontWeight: 'bold',
    color: palette.text,
    marginBottom: 6,
    textAlign: 'center',
    lineHeight: 36,
  },
  subtitle: {
    fontSize: 17,
    color: palette.text,
    textAlign: 'center',
    opacity: 0.72,
    maxWidth: 290,
    lineHeight: 24,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingHorizontal: 18,
  },
  xpBubble: {
    backgroundColor: 'rgba(255,255,255,0.6)',
    borderRadius: 28,
    paddingVertical: 10,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 4,
    minWidth: 70,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.38)',
  },
  xpNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: palette.text,
  },
  xpLabel: {
    fontSize: 12,
    color: palette.text,
    opacity: 0.75,
    fontWeight: '600',
  },
  logoutButton: {
    backgroundColor: palette.text,
    borderRadius: 18,
    paddingVertical: 10,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.16,
    shadowRadius: 10,
    elevation: 4,
  },
  logoutText: {
    color: palette.background,
    fontSize: 14,
    fontWeight: 'bold',
  },
  welcomeSection: {
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingBottom: 28,
  },
  welcomeBadge: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.58)',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.42)',
  },
  welcomeBadgeText: {
    color: palette.text,
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.3,
    opacity: 0.72,
    textTransform: 'uppercase',
  },
  meta: {
    fontSize: 14,
    color: palette.text,
    marginBottom: 16,
  },
  streakBubble: {
    backgroundColor: 'rgba(255,255,255,0.6)',
    borderRadius: 28,
    paddingVertical: 8,
    paddingHorizontal: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 4,
    minWidth: 70,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.38)',
  },
  streakNumber: {
    fontSize: 26,
    fontWeight: 'bold',
  },
  streakLabel: {
    fontSize: 12,
    color: palette.text,
    opacity: 0.75,
    fontWeight: '600',
  },
  list: {
    paddingTop: 8,
    paddingBottom: 28,
  },
  lessonTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: palette.text,
    marginBottom: 6,
  },
  lessonDescription: {
    fontSize: 14,
    color: palette.text,
    marginBottom: 8,
  },
  lessonMeta: {
    fontSize: 12,
    color: palette.text,
    opacity: 0.75,
  },
  lessonWrapper: {
    marginBottom: 16,
    alignItems: 'center',
  },
  backgroundGlowTop: {
    position: 'absolute',
    top: -40,
    left: -40,
    width: 220,
    height: 220,
    borderRadius: 999,
    backgroundColor: '#DCE8F1',
    opacity: 0.8,
  },
  backgroundGlowBottom: {
    position: 'absolute',
    right: -50,
    bottom: 80,
    width: 240,
    height: 240,
    borderRadius: 999,
    backgroundColor: palette.accent,
    opacity: 0.18,
  },
  heroPanel: {
    backgroundColor: '#D4E0E8',
    borderRadius: 34,
    marginBottom: 18,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.45)',
    shadowColor: '#5B6C82',
    shadowOffset: { width: 0, height: 18 },
    shadowOpacity: 0.12,
    shadowRadius: 28,
    elevation: 8,
  },
  heroSafeArea: {
    paddingTop: 4,
  },
  heroBlurOrb: {
    position: 'absolute',
    backgroundColor: 'rgba(255,255,255,0.42)',
    borderRadius: 999,
  },
  heroBlurOrbLarge: {
    width: 220,
    height: 220,
    top: -36,
    right: -70,
  },
  heroBlurOrbMedium: {
    width: 130,
    height: 130,
    bottom: 26,
    left: -18,
    opacity: 0.5,
  },
  heroBlurOrbSmall: {
    width: 96,
    height: 96,
    top: 116,
    right: 48,
    opacity: 0.45,
  },
  skyCloud: {
    position: 'absolute',
    backgroundColor: palette.background,
    borderRadius: 200,
    opacity: 0.3,
  },
  lessonCloud: {
    width: '92%',
    minHeight: 120,
    backgroundColor: 'rgba(255,255,255,0.92)',
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    shadowColor: '#5B6C82',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 20,
    elevation: 6,
    borderWidth: 1,
    borderColor: 'rgba(209,217,223,0.9)',
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
    color: palette.text,
    zIndex: 2,
    textAlign: 'center',
  },
  lessonMetaCloud: {
    fontSize: 13,
    color: palette.text,
    zIndex: 2,
    marginTop: 8,
    textAlign: 'center',
    opacity: 0.7,
  },

  cloudBase: {
    position: 'absolute',
    bottom: 8,
    width: '100%',
    height: 62,
    backgroundColor: palette.background,
    borderRadius: 32,
  },
  cloudBump: {
    position: 'absolute',
    top: 0,
    width: 80,
    height: 80,
    backgroundColor: palette.background,
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
    color: palette.text,
    textAlign: 'center',
    marginTop: 16,
  },
  emptyText: {
    color: palette.text,
    textAlign: 'center',
    marginTop: 20,
    fontSize: 16,
  },
  button: {
    marginTop: 12,
    backgroundColor: palette.text,
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    alignSelf: 'center',
  },
  buttonText: {
    color: palette.background,
    fontSize: 18,
    fontWeight: 'bold',
  },
});
