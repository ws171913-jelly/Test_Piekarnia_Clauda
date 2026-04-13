/**
 * Mock dla react-native-mmkv — prosty in-memory storage.
 */
const store: Record<string, string> = {};

export class MMKV {
  constructor(_config?: { id?: string }) {}

  set(key: string, value: string): void {
    store[key] = value;
  }

  getString(key: string): string | undefined {
    return store[key];
  }

  delete(key: string): void {
    delete store[key];
  }

  clearAll(): void {
    Object.keys(store).forEach((k) => delete store[k]);
  }
}
