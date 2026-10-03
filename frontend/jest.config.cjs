module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  moduleNameMapper: {'\\.(css)$': 'identity-obj-proxy'},
  transform: {'^.+\\.(ts|tsx)$': ['ts-jest', {tsconfig: 'tsconfig.test.json'}]}
};
