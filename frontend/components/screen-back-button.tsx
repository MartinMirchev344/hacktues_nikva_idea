import { Href, useRouter } from 'expo-router';
import { StyleSheet, Text, TouchableOpacity, ViewStyle } from 'react-native';
import { palette } from '../constants/colors';

type ScreenBackButtonProps = {
  fallbackHref: Href;
  label?: string;
  style?: ViewStyle;
};

export function ScreenBackButton({
  fallbackHref,
  label = 'Back',
  style,
}: ScreenBackButtonProps) {
  const router = useRouter();

  const handlePress = () => {
    if (router.canGoBack()) {
      router.back();
      return;
    }

    router.replace(fallbackHref);
  };

  return (
    <TouchableOpacity
      accessibilityLabel={label}
      accessibilityRole="button"
      activeOpacity={0.85}
      onPress={handlePress}
      style={[styles.button, style]}
    >
      <Text style={styles.arrow}>←</Text>
      <Text style={styles.label}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: palette.surface,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 6,
    elevation: 3,
  },
  arrow: {
    fontSize: 20,
    fontWeight: '700',
    color: palette.text,
    lineHeight: 22,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: palette.text,
  },
});
