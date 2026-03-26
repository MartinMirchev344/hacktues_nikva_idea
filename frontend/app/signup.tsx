import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useEffect, useState } from 'react';
import { Link, useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../context/auth-context';
import { login, register } from '../lib/auth-api';

export default function Auth() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mode?: string }>();
  const { setAuth } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (params.mode === 'signup') {
      setIsLogin(false);
      return;
    }
    if (params.mode === 'login') {
      setIsLogin(true);
    }
  }, [params.mode]);

  const handleAuth = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    if (!isLogin && password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    try {
      setIsSubmitting(true);
      const authResponse = isLogin
        ? await login({ email, password })
        : await register({ email, password, confirmPassword });
      setAuth(authResponse);
      Alert.alert('Success', `${isLogin ? 'Logged in' : 'Account created'} successfully!`);
      router.replace('/home');
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to authenticate right now.';
      Alert.alert('Error', message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.formContainer}>
        <Text style={styles.title}>Unspoken</Text>
        <Text style={styles.subtitle}>{isLogin ? 'Welcome Back' : 'Create Account'}</Text>
        
        <View style={styles.tabContainer}>
          <TouchableOpacity 
            style={[styles.tab, isLogin && styles.activeTab]} 
            onPress={() => setIsLogin(true)}
          >
            <Text style={[styles.tabText, isLogin && styles.activeTabText]}>Log In</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.tab, !isLogin && styles.activeTab]} 
            onPress={() => setIsLogin(false)}
          >
            <Text style={[styles.tabText, !isLogin && styles.activeTabText]}>Sign Up</Text>
          </TouchableOpacity>
        </View>

        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor="#6D7A71"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#6D7A71"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        {!isLogin && (
          <TextInput
            style={styles.input}
            placeholder="Confirm Password"
            placeholderTextColor="#6D7A71"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
          />
        )}

        <TouchableOpacity
          style={[styles.button, isSubmitting && styles.buttonDisabled]}
          onPress={handleAuth}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color="#EFEADD" />
          ) : (
            <Text style={styles.buttonText}>{isLogin ? 'Log In' : 'Sign Up'}</Text>
          )}
        </TouchableOpacity>

        <Link href="/" style={styles.backLink}>
          <Text style={styles.backLinkText}>Back to Home</Text>
        </Link>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#EFEADD',
    justifyContent: 'center',
  },
  formContainer: {
    backgroundColor: '#CDD9C5',
    margin: 20,
    borderRadius: 20,
    padding: 30,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#6D7A71',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#BA806A',
    textAlign: 'center',
    marginBottom: 30,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#E8D7C7',
    borderRadius: 25,
    padding: 4,
    marginBottom: 30,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 21,
  },
  activeTab: {
    backgroundColor: '#BA806A',
  },
  tabText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6D7A71',
  },
  activeTabText: {
    color: '#EFEADD',
  },
  input: {
    backgroundColor: '#EFEADD',
    borderWidth: 2,
    borderColor: '#6D7A71',
    padding: 15,
    marginBottom: 15,
    borderRadius: 12,
    fontSize: 16,
    color: '#6D7A71',
  },
  button: {
    backgroundColor: '#BA806A',
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: '#EFEADD',
    fontSize: 18,
    fontWeight: 'bold',
  },
  backLink: {
    alignSelf: 'center',
    marginTop: 20,
  },
  backLinkText: {
    color: '#6D7A71',
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});
