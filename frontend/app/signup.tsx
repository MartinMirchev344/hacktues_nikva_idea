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
import { Redirect, useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../context/auth-context';
import { login, register } from '../lib/auth-api';
import { palette } from '../constants/colors';

export default function Auth() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mode?: string }>();
  const { auth, isHydrating, setAuth } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (params.mode === 'signup') {
      setIsLogin(false);
      setErrorMessage('');
      return;
    }
    if (params.mode === 'login') {
      setIsLogin(true);
      setErrorMessage('');
    }
  }, [params.mode]);

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

  const handleAuth = async () => {
    if (
      !email.trim() ||
      !password ||
      (!isLogin && (!username.trim() || !confirmPassword))
    ) {
      setErrorMessage('Please fill in all fields.');
      return;
    }
    if (!isLogin && password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage('');
      const authResponse = isLogin
        ? await login({ email: email.trim(), password })
        : await register({
            username: username.trim(),
            email: email.trim(),
            password,
            confirmPassword,
          });
      setAuth(authResponse);
      Alert.alert('Success', `${isLogin ? 'Logged in' : 'Account created'} successfully!`);
      router.replace('/home');
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to authenticate right now.';
      setErrorMessage(message);
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
            onPress={() => {
              setIsLogin(true);
              setErrorMessage('');
            }}
          >
            <Text style={[styles.tabText, isLogin && styles.activeTabText]}>Log In</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.tab, !isLogin && styles.activeTab]} 
            onPress={() => {
              setIsLogin(false);
              setErrorMessage('');
            }}
          >
            <Text style={[styles.tabText, !isLogin && styles.activeTabText]}>Sign Up</Text>
          </TouchableOpacity>
        </View>

        {!isLogin && (
          <TextInput
            style={styles.input}
            placeholder="Username"
            placeholderTextColor={palette.text}
            value={username}
            onChangeText={(value) => {
              setUsername(value);
              if (errorMessage) {
                setErrorMessage('');
              }
            }}
            autoCapitalize="none"
          />
        )}
        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor={palette.text}
          value={email}
          onChangeText={(value) => {
            setEmail(value);
            if (errorMessage) {
              setErrorMessage('');
            }
          }}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor={palette.text}
          value={password}
          onChangeText={(value) => {
            setPassword(value);
            if (errorMessage) {
              setErrorMessage('');
            }
          }}
          secureTextEntry
        />
        {!isLogin && (
          <TextInput
            style={styles.input}
            placeholder="Confirm Password"
            placeholderTextColor={palette.text}
            value={confirmPassword}
            onChangeText={(value) => {
              setConfirmPassword(value);
              if (errorMessage) {
                setErrorMessage('');
              }
            }}
            secureTextEntry
          />
        )}

        {!!errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

        <TouchableOpacity
          style={[styles.button, isSubmitting && styles.buttonDisabled]}
          onPress={handleAuth}
          disabled={isSubmitting}
        >
          {isSubmitting ? (
            <ActivityIndicator color={palette.background} />
          ) : (
            <Text style={styles.buttonText}>{isLogin ? 'Log In' : 'Sign Up'}</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: palette.background,
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: palette.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  formContainer: {
    backgroundColor: palette.surface,
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
    color: palette.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: palette.text,
    textAlign: 'center',
    marginBottom: 30,
    opacity: 0.8,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: palette.background,
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
    backgroundColor: palette.accent,
  },
  tabText: {
    fontSize: 16,
    fontWeight: '600',
    color: palette.text,
    opacity: 0.75,
  },
  activeTabText: {
    color: palette.text,
    opacity: 1,
  },
  input: {
    backgroundColor: palette.background,
    borderWidth: 1.5,
    borderColor: palette.accent,
    padding: 15,
    marginBottom: 15,
    borderRadius: 12,
    fontSize: 16,
    color: palette.text,
  },
  errorText: {
    color: '#B00020',
    fontSize: 14,
    marginBottom: 8,
    marginTop: -4,
    textAlign: 'center',
  },
  button: {
    backgroundColor: palette.text,
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: palette.background,
    fontSize: 18,
    fontWeight: 'bold',
  },
});
