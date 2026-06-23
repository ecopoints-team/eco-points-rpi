/**
 * Jest setup shim: adds clearMocksOnScope to jest-mock@29's ModuleMocker prototype.
 * Required because react-native pulls in jest-environment-node with jest-mock@29
 * which lacks this method introduced in jest-mock@30.
 *
 * We patch BOTH the top-level jest-mock and react-native's nested jest-mock
 * so that whichever instance jest-runtime's _moduleMocker resolves to has
 * the method available.
 */

function patchModuleMocker(jestMock) {
  if (jestMock && jestMock.ModuleMocker && !jestMock.ModuleMocker.prototype.clearMocksOnScope) {
    jestMock.ModuleMocker.prototype.clearMocksOnScope = function clearMocksOnScope(scope) {
      for (const key of Object.keys(scope)) {
        const value = scope[key];
        if (
          value != null &&
          (typeof value === 'object' || typeof value === 'function') &&
          '_isMockFunction' in value &&
          this.isMockFunction(value) &&
          typeof value.mockClear === 'function'
        ) {
          value.mockClear();
        }
      }
    };
  }
}

// Patch the top-level jest-mock (used by most of the jest ecosystem)
try {
  patchModuleMocker(require('jest-mock'));
} catch (_) {}

// Patch react-native's nested jest-mock@29 (used by react-native/jest/react-native-env.js
// which is the testEnvironment set by jest-expo's preset via react-native/jest-preset.js)
try {
  patchModuleMocker(require('react-native/node_modules/jest-mock'));
} catch (_) {}
