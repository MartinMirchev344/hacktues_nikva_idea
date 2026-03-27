export const SIGNASL_VIDREFS: Record<string, string> = {
  // Alphabet
  a: 'l93ttye86c',
  f: 'gpogljtucn',
  k: 'vbnj34s7g4',
  r: 'bgjlnba0uz',
  w: 'uzumydfhfg',
  // Greetings
  hello: 'ns3nvo9mpj',
  goodbye: '1jqvdn4kow',
  thank_you: 'pdmmfefdff',
  please: 'nti5jzikz6',
  sorry: 'thdxo8twup',
  // Yes & No
  yes: 'pqgak01sun',
  no: '0vycdillx8',
  maybe: 'byblzeix7t',
  // Numbers 1–5
  one: 'mxwf7kphpz',
  two: '9kxdliygm5',
  three: 'vqnue9bgxe',
  four: 'kxamml6ogh',
  five: 'hf91kna1ai',
  // Numbers 6–10
  six: 'ljij2w0mxs',
  seven: 'ovak0dmbuq',
  eight: '8zew4o1lrb',
  nine: 'wmywtcyb4j',
  ten: 'jnpdtpmo9l',
  // Family
  mother: 'xhumgambd0',
  father: 'wg99m7o6om',
  brother: 'shmgffyrlm',
  sister: 'cj5wxieev1',
  friend: 'y0copmlysx',
  // Colors
  red: 'vhxdhxljbc',
  blue: 'fxqwepxm7j',
  green: 'k0p9cpqpzy',
  yellow: 'yxvqepltwd',
  white: 'zspnng9zo5',
  black: 'vkokqksf6v',
  // Feelings
  happy: 'upqz5ebm4n',
  sad: 'idzih4ih1g',
  angry: '0twdyiqkgd',
  tired: 'pjvijjq1zx',
  love: 'tej0m2zew3',
  // Common Questions
  what: '7ou1bjsait',
  where: 'sibioxossa',
  who: 'oco0msxi7x',
  when: 'awxr8ofuol',
  how: '8ksemb7sgk',
  // Food & Drink
  eat: 'kpyrqtjqsr',
  drink: 'bhmijdp3cz',
  water: 'zx36azvpcf',
  more: 'qyegtcfc7a',
  finished: '24ghxkesl4',
  // Asking for Help
  help: 'shpdlzz5rp',
  stop: 'h7gy7mrrjr',
  wait: 'oxrmaeaxsl',
  understand: 'ibnpmkklcq',
};

export function getVidref(expectedSign: string): string | null {
  const key = expectedSign.toLowerCase().replace(/ /g, '_').replace(/-/g, '_');
  return SIGNASL_VIDREFS[key] ?? null;
}
