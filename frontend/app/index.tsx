import { View, ActivityIndicator, StyleSheet } from 'react-native';
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

  return <Redirect href={{ pathname: '/signup', params: { mode: 'login' } }} />;
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: palette.background,
  },
});
