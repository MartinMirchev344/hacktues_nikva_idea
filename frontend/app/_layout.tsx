import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AuthProvider } from '../context/auth-context';

export default function RootLayout() {
  return (
    <AuthProvider>
      <SafeAreaProvider>
        <Stack>
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="signup" options={{ headerShown: false }} />
          <Stack.Screen name="home" options={{ headerShown: false }} />
          <Stack.Screen name="lessons/[slug]" options={{ headerShown: false }} />
          <Stack.Screen name="exercise/[id]" options={{ headerShown: false }} />
        </Stack>
        <StatusBar style="dark" />
      </SafeAreaProvider>
    </AuthProvider>
  );
}
