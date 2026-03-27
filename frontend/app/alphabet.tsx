import { useRef, useEffect } from 'react';
import {
  Animated,
  Easing,
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  ScrollView,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { Stack, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/auth-context';
import { palette } from '../constants/colors';

function streakColor(streak: number): string {
  if (streak <= 0) return '#AAAAAA';
  const stops = ['#FF6600', '#CC0000', '#0055FF', '#7B00CC'];
  const total = stops.length - 1;
  const t = Math.min(streak / 30, 1) * total;
  const i = Math.min(Math.floor(t), total - 1);
  const f = t - i;
  const hex = (h: string) => [parseInt(h.slice(1,3),16), parseInt(h.slice(3,5),16), parseInt(h.slice(5,7),16)];
  const [r1,g1,b1] = hex(stops[i]);
  const [r2,g2,b2] = hex(stops[i+1]);
  return `rgb(${Math.round(r1+(r2-r1)*f)},${Math.round(g1+(g2-g1)*f)},${Math.round(b1+(b2-b1)*f)})`;
}

function FlameIcon({ streak }: { streak: number }) {
  const color = streakColor(streak);
  return (
    <Svg width={38} height={46} viewBox="0 0 24 30">
      <Path d="M12 28 C6 25 2 20 2 14 C2 9 5 5 8 2 C8 6 10 8 12 9 C12 6 14 3 16 1 C18 5 22 9 22 14 C22 20 18 25 12 28 Z" fill={color} opacity={0.9} />
      <Path d="M12 25 C9 22 8 18 9 14 C10 16 11 17 12 17 C13 15 13 12 14 10 C15 13 16 17 15 21 C14 23 13 24 12 25 Z" fill="rgba(255,255,255,0.35)" />
    </Svg>
  );
}

export default function Alphabet() {
  const router = useRouter();
  const { auth, logout } = useAuth();

  const floatAnim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, { toValue: 1, duration: 3200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(floatAnim, { toValue: 0, duration: 3200, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    ).start();
  }, [floatAnim]);

  const skyClouds = [
    { top: 60, left: 14, width: 100, height: 58 },
    { top: 26, right: 24, width: 130, height: 64 },
    { top: 170, left: 8, width: 86, height: 48 },
  ];

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ headerShown: false }} />

      <View style={styles.backgroundGlowTop} />
      <View style={styles.backgroundGlowBottom} />

      <View style={styles.heroPanel}>
        <View style={[styles.heroBlurOrb, styles.heroBlurOrbLarge]} />
        <View style={[styles.heroBlurOrb, styles.heroBlurOrbMedium]} />
        <View style={[styles.heroBlurOrb, styles.heroBlurOrbSmall]} />
        {skyClouds.map((c, i) => (
          <View key={i} style={[styles.skyCloud, c]} />
        ))}

        <SafeAreaView edges={['top']} style={styles.heroSafeArea}>
          <View style={styles.headerRow}>
            <View style={styles.xpBubble}>
              <Text style={styles.xpNumber}>{auth?.user.xp ?? 0}</Text>
              <Text style={styles.xpLabel}>XP</Text>
            </View>
            <View style={styles.streakBubble}>
              <FlameIcon streak={auth?.user.streak ?? 0} />
              <Text style={[styles.streakNumber, { color: streakColor(auth?.user.streak ?? 0) }]}>
                {auth?.user.streak ?? 0}
              </Text>
            </View>
            <TouchableOpacity style={styles.logoutButton} onPress={() => { logout(); router.replace('/'); }}>
              <Text style={styles.logoutText}>Log Out</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>

        <View style={styles.welcomeSection}>
          <TouchableOpacity style={styles.welcomeBadge} onPress={() => router.replace('/home')}>
            <Text style={styles.welcomeBadgeText}>← Back to Lessons</Text>
          </TouchableOpacity>
          <Text style={styles.welcome}>ASL Alphabet</Text>
          <Text style={styles.subtitle}>Reference chart for all 26 letters</Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.chartWrapper}>
          <Image
            source={require('../assets/asl-alphabet.png')}
            style={styles.chart}
            resizeMode="contain"
          />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: palette.background,
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  backgroundGlowTop: {
    position: 'absolute',
    top: -40, left: -40,
    width: 220, height: 220,
    borderRadius: 999,
    backgroundColor: '#DCE8F1',
    opacity: 0.8,
  },
  backgroundGlowBottom: {
    position: 'absolute',
    right: -50, bottom: 80,
    width: 240, height: 240,
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
  heroBlurOrbLarge: { width: 220, height: 220, top: -36, right: -70 },
  heroBlurOrbMedium: { width: 130, height: 130, bottom: 26, left: -18, opacity: 0.5 },
  heroBlurOrbSmall: { width: 96, height: 96, top: 116, right: 48, opacity: 0.45 },
  skyCloud: {
    position: 'absolute',
    backgroundColor: palette.background,
    borderRadius: 200,
    opacity: 0.3,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    paddingHorizontal: 16,
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
  xpNumber: { fontSize: 24, fontWeight: 'bold', color: palette.text },
  xpLabel: { fontSize: 12, color: palette.text, opacity: 0.75, fontWeight: '600' },
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
  streakNumber: { fontSize: 26, fontWeight: 'bold' },
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
  logoutText: { color: palette.background, fontSize: 14, fontWeight: 'bold' },
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
  welcome: {
    fontSize: 28,
    fontWeight: 'bold',
    color: palette.text,
    marginBottom: 4,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: palette.text,
    opacity: 0.75,
    textAlign: 'center',
  },
  scroll: {
    paddingBottom: 40,
  },
  chartWrapper: {
    backgroundColor: 'rgba(255,255,255,0.92)',
    borderRadius: 20,
    padding: 12,
    shadowColor: '#5B6C82',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 20,
    elevation: 6,
    borderWidth: 1,
    borderColor: 'rgba(209,217,223,0.9)',
  },
  chart: {
    width: '100%',
    aspectRatio: 0.8,
  },
});
