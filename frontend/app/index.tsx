import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Link } from 'expo-router';
import { Redirect } from 'expo-router';
import { useAuth } from '../context/auth-context';
import { palette } from '../constants/colors';

export default function Index() {
  const { auth, isHydrating } = useAuth();

  if (isHydrating) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={palette.text} />
      </View>
    );
  }

  if (auth) {
    return <Redirect href="/home" />;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to Unspoken</Text>
      <Text style={styles.subtitle}>Sign in or sign up to continue</Text>
      <View style={styles.buttonContainer}>
        <Link href={{ pathname: '/signup', params: { mode: 'login' } }} asChild>
          <TouchableOpacity style={styles.button}>
            <Text style={styles.buttonText}>Log In</Text>
          </TouchableOpacity>
        </Link>
        <Link href={{ pathname: '/signup', params: { mode: 'signup' } }} asChild>
          <TouchableOpacity style={styles.button}>
            <Text style={styles.buttonText}>Sign Up</Text>
          </TouchableOpacity>
        </Link>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: palette.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.background,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: palette.text,
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    color: palette.text,
    marginBottom: 40,
    textAlign: 'center',
    opacity: 0.8,
  },
  buttonContainer: {
    width: '100%',
    gap: 15,
  },
  button: {
    backgroundColor: palette.accent,
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  buttonText: {
    color: palette.text,
    fontSize: 18,
    fontWeight: 'bold',
  },
});
