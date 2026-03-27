import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { useEffect, useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { Redirect, useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../context/auth-context';
import { login, register, verifyLoginOtp, forgotPassword, resetPassword } from '../lib/auth-api';
import { palette } from '../constants/colors';

type Step = 'credentials' | 'otp' | 'forgot-email' | 'forgot-reset';

export default function Auth() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mode?: string }>();
  const { auth, isHydrating, setAuth } = useAuth();

  const [isLogin, setIsLogin] = useState(true);
  const [step, setStep] = useState<Step>('credentials');

  // Credentials form
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // OTP step
  const [otpEmail, setOtpEmail] = useState('');
  const [otpCode, setOtpCode] = useState('');

  // Forgot password
  const [forgotEmail, setForgotEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [showConfirmNewPassword, setShowConfirmNewPassword] = useState(false);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

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

  const clearErrors = () => {
    setErrorMessage('');
    setInfoMessage('');
  };

  const handleAuth = async () => {
    if (!email.trim() || !password || (!isLogin && (!username.trim() || !confirmPassword))) {
      setErrorMessage('Please fill in all fields.');
      return;
    }
    if (!isLogin && password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      clearErrors();

      if (!isLogin) {
        const authResponse = await register({
          username: username.trim(),
          email: email.trim(),
          password,
          confirmPassword,
        });
        setAuth(authResponse);
        router.replace('/home');
        return;
      }

      const response = await login({ email: email.trim(), password });
      if ('needs_otp' in response && response.needs_otp) {
        setOtpEmail(response.email);
        setOtpCode('');
        setStep('otp');
      } else {
        setAuth(response);
        router.replace('/home');
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to authenticate right now.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (otpCode.length !== 6) {
      setErrorMessage('Please enter the 6-digit code.');
      return;
    }
    try {
      setIsSubmitting(true);
      clearErrors();
      const authResponse = await verifyLoginOtp(otpEmail, otpCode);
      setAuth(authResponse);
      router.replace('/home');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Verification failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendLoginOtp = async () => {
    try {
      clearErrors();
      await login({ email: otpEmail, password });
      setInfoMessage('A new code has been sent to your email.');
    } catch {
      setErrorMessage('Failed to resend code.');
    }
  };

  const handleForgotSubmit = async () => {
    if (!forgotEmail.trim()) {
      setErrorMessage('Please enter your email.');
      return;
    }
    try {
      setIsSubmitting(true);
      clearErrors();
      await forgotPassword(forgotEmail.trim());
      setOtpEmail(forgotEmail.trim());
      setResetCode('');
      setNewPassword('');
      setConfirmNewPassword('');
      setStep('forgot-reset');
      setInfoMessage('Check your email for the reset code.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Something went wrong.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async () => {
    if (resetCode.length !== 6) {
      setErrorMessage('Please enter the 6-digit code.');
      return;
    }
    if (!newPassword || !confirmNewPassword) {
      setErrorMessage('Please fill in all fields.');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }
    try {
      setIsSubmitting(true);
      clearErrors();
      const authResponse = await resetPassword(otpEmail, resetCode, newPassword);
      setAuth(authResponse);
      router.replace('/home');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Reset failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendReset = async () => {
    try {
      clearErrors();
      await forgotPassword(otpEmail);
      setInfoMessage('A new code has been sent to your email.');
    } catch {
      setErrorMessage('Failed to resend code.');
    }
  };

  // ── OTP screen ──────────────────────────────────────────────────────────────
  if (step === 'otp') {
    return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={styles.formContainer}>
          <Text style={styles.title}>Check Your Email</Text>
          <Text style={styles.subtitle}>
            We sent a 6-digit code to{'\n'}
            <Text style={styles.emailHighlight}>{otpEmail}</Text>
          </Text>

          <TextInput
            style={[styles.input, styles.otpInput]}
            placeholder="000000"
            placeholderTextColor={palette.text}
            value={otpCode}
            onChangeText={(v) => { setOtpCode(v.replace(/\D/g, '').slice(0, 6)); clearErrors(); }}
            keyboardType="number-pad"
            maxLength={6}
            textAlign="center"
          />

          {!!errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}
          {!!infoMessage && <Text style={styles.infoText}>{infoMessage}</Text>}

          <TouchableOpacity
            style={[styles.button, isSubmitting && styles.buttonDisabled]}
            onPress={handleVerifyOtp}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color={palette.background} />
            ) : (
              <Text style={styles.buttonText}>Verify</Text>
            )}
          </TouchableOpacity>

          <View style={styles.linkRow}>
            <TouchableOpacity onPress={handleResendLoginOtp}>
              <Text style={styles.linkText}>Resend code</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => { setStep('credentials'); clearErrors(); }}>
              <Text style={styles.linkText}>Back to login</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    );
  }

  // ── Forgot password: enter email ─────────────────────────────────────────────
  if (step === 'forgot-email') {
    return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={styles.formContainer}>
          <Text style={styles.title}>Forgot Password</Text>
          <Text style={styles.subtitle}>Enter your email and we'll send you a reset code.</Text>

          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor={palette.text}
            value={forgotEmail}
            onChangeText={(v) => { setForgotEmail(v); clearErrors(); }}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          {!!errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}

          <TouchableOpacity
            style={[styles.button, isSubmitting && styles.buttonDisabled]}
            onPress={handleForgotSubmit}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color={palette.background} />
            ) : (
              <Text style={styles.buttonText}>Send Code</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity style={styles.backLink} onPress={() => { setStep('credentials'); clearErrors(); }}>
            <Text style={styles.linkText}>Back to login</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    );
  }

  // ── Forgot password: enter code + new password ────────────────────────────────
  if (step === 'forgot-reset') {
    return (
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={styles.formContainer}>
          <Text style={styles.title}>Reset Password</Text>
          <Text style={styles.subtitle}>
            Enter the code sent to{'\n'}
            <Text style={styles.emailHighlight}>{otpEmail}</Text>
          </Text>

          <TextInput
            style={[styles.input, styles.otpInput]}
            placeholder="000000"
            placeholderTextColor={palette.text}
            value={resetCode}
            onChangeText={(v) => { setResetCode(v.replace(/\D/g, '').slice(0, 6)); clearErrors(); }}
            keyboardType="number-pad"
            maxLength={6}
            textAlign="center"
          />

          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              placeholder="New Password"
              placeholderTextColor={palette.text}
              value={newPassword}
              onChangeText={(v) => { setNewPassword(v); clearErrors(); }}
              secureTextEntry={!showNewPassword}
            />
            <TouchableOpacity style={styles.eyeButton} onPress={() => setShowNewPassword(p => !p)}>
              <Ionicons name={showNewPassword ? 'eye-off' : 'eye'} size={22} color={palette.text} />
            </TouchableOpacity>
          </View>

          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              placeholder="Confirm New Password"
              placeholderTextColor={palette.text}
              value={confirmNewPassword}
              onChangeText={(v) => { setConfirmNewPassword(v); clearErrors(); }}
              secureTextEntry={!showConfirmNewPassword}
            />
            <TouchableOpacity style={styles.eyeButton} onPress={() => setShowConfirmNewPassword(p => !p)}>
              <Ionicons name={showConfirmNewPassword ? 'eye-off' : 'eye'} size={22} color={palette.text} />
            </TouchableOpacity>
          </View>

          {!!errorMessage && <Text style={styles.errorText}>{errorMessage}</Text>}
          {!!infoMessage && <Text style={styles.infoText}>{infoMessage}</Text>}

          <TouchableOpacity
            style={[styles.button, isSubmitting && styles.buttonDisabled]}
            onPress={handleResetPassword}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color={palette.background} />
            ) : (
              <Text style={styles.buttonText}>Reset Password</Text>
            )}
          </TouchableOpacity>

          <View style={styles.linkRow}>
            <TouchableOpacity onPress={handleResendReset}>
              <Text style={styles.linkText}>Resend code</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => { setStep('credentials'); clearErrors(); }}>
              <Text style={styles.linkText}>Back to login</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    );
  }

  // ── Main credentials screen ──────────────────────────────────────────────────
  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.formContainer}>
        <Text style={styles.title}>Mimical</Text>
        <Text style={styles.subtitle}>{isLogin ? 'Welcome Back' : 'Create Account'}</Text>

        <View style={styles.tabContainer}>
          <TouchableOpacity
            style={[styles.tab, isLogin && styles.activeTab]}
            onPress={() => { setIsLogin(true); clearErrors(); }}
          >
            <Text style={[styles.tabText, isLogin && styles.activeTabText]}>Log In</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.tab, !isLogin && styles.activeTab]}
            onPress={() => { setIsLogin(false); clearErrors(); }}
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
            onChangeText={(v) => { setUsername(v); clearErrors(); }}
            autoCapitalize="none"
          />
        )}

        <TextInput
          style={styles.input}
          placeholder="Email"
          placeholderTextColor={palette.text}
          value={email}
          onChangeText={(v) => { setEmail(v); clearErrors(); }}
          keyboardType="email-address"
          autoCapitalize="none"
        />

        <View style={styles.passwordRow}>
          <TextInput
            style={[styles.input, styles.passwordInput]}
            placeholder="Password"
            placeholderTextColor={palette.text}
            value={password}
            onChangeText={(v) => { setPassword(v); clearErrors(); }}
            secureTextEntry={!showPassword}
          />
          <TouchableOpacity style={styles.eyeButton} onPress={() => setShowPassword(p => !p)}>
            <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={22} color={palette.text} />
          </TouchableOpacity>
        </View>

        {!isLogin && (
          <View style={styles.passwordRow}>
            <TextInput
              style={[styles.input, styles.passwordInput]}
              placeholder="Confirm Password"
              placeholderTextColor={palette.text}
              value={confirmPassword}
              onChangeText={(v) => { setConfirmPassword(v); clearErrors(); }}
              secureTextEntry={!showConfirmPassword}
            />
            <TouchableOpacity style={styles.eyeButton} onPress={() => setShowConfirmPassword(p => !p)}>
              <Ionicons name={showConfirmPassword ? 'eye-off' : 'eye'} size={22} color={palette.text} />
            </TouchableOpacity>
          </View>
        )}

        {isLogin && (
          <TouchableOpacity
            style={styles.forgotLink}
            onPress={() => { setForgotEmail(email.trim()); setStep('forgot-email'); clearErrors(); }}
          >
            <Text style={styles.linkText}>Forgot password?</Text>
          </TouchableOpacity>
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
    fontSize: 16,
    color: palette.text,
    textAlign: 'center',
    marginBottom: 24,
    opacity: 0.8,
    lineHeight: 22,
  },
  emailHighlight: {
    fontWeight: 'bold',
    opacity: 1,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: palette.background,
    borderRadius: 25,
    padding: 4,
    marginBottom: 24,
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
  passwordRow: {
    position: 'relative',
    marginBottom: 0,
  },
  passwordInput: {
    paddingRight: 52,
    marginBottom: 15,
  },
  eyeButton: {
    position: 'absolute',
    right: 14,
    top: 14,
    padding: 2,
  },
  otpInput: {
    fontSize: 28,
    fontWeight: 'bold',
    letterSpacing: 8,
    textAlign: 'center',
    marginBottom: 15,
  },
  forgotLink: {
    alignSelf: 'flex-end',
    marginTop: -8,
    marginBottom: 12,
  },
  backLink: {
    alignItems: 'center',
    marginTop: 12,
  },
  linkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 14,
  },
  linkText: {
    color: palette.text,
    fontSize: 14,
    fontWeight: '600',
    opacity: 0.7,
    textDecorationLine: 'underline',
  },
  errorText: {
    color: '#B00020',
    fontSize: 14,
    marginBottom: 8,
    textAlign: 'center',
  },
  infoText: {
    color: '#1a7a1a',
    fontSize: 14,
    marginBottom: 8,
    textAlign: 'center',
  },
  button: {
    backgroundColor: palette.text,
    paddingVertical: 15,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 4,
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
