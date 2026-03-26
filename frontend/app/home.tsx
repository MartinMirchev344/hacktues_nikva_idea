import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Redirect, useRouter } from 'expo-router';
import { useAuth } from '../context/auth-context';

export default function Home() {
  const router = useRouter();
  const { auth, logout } = useAuth();

  if (!auth) {
    return <Redirect href="/signup" />;
  }

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome, {auth.user.username}</Text>
      <Text style={styles.subtitle}>You are logged in and ready to use the app.</Text>
      <Text style={styles.meta}>Email: {auth.user.email}</Text>
      <Text style={styles.meta}>XP: {auth.user.xp}</Text>
      <TouchableOpacity style={styles.button} onPress={handleLogout}>
        <Text style={styles.buttonText}>Log Out</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#EFEADD',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#6D7A71',
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 18,
    color: '#BA806A',
    marginBottom: 24,
    textAlign: 'center',
  },
  meta: {
    fontSize: 16,
    color: '#6D7A71',
    marginBottom: 8,
  },
  button: {
    marginTop: 24,
    backgroundColor: '#BA806A',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
  },
  buttonText: {
    color: '#EFEADD',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
