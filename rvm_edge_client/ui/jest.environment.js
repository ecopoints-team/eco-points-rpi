/**
 * Custom Jest environment that extends the react-native env and patches
 * jest-mock@29's ModuleMocker instance to add clearMocksOnScope.
 *
 * This is necessary because react-native bundles jest-mock@29 which lacks
 * clearMocksOnScope, but jest-runtime@30 calls it in resetModules().
 */
'use strict';

const ReactNativeEnv = require('react-native/jest/react-native-env');

function patchModuleMocker(mocker) {
  if (mocker && !mocker.clearMocksOnScope) {
    mocker.clearMocksOnScope = function clearMocksOnScope(scope) {
      let keys;
      try {
        keys = Object.keys(scope);
      } catch (_) {
        return;
      }
      for (const key of keys) {
        let value;
        try {
          // Use hasOwnProperty to avoid triggering prototype getters
          if (!Object.prototype.hasOwnProperty.call(scope, key)) continue;
          // Get the property descriptor to avoid triggering lazy getters
          const descriptor = Object.getOwnPropertyDescriptor(scope, key);
          if (!descriptor || typeof descriptor.get === 'function') continue;
          value = descriptor.value;
        } catch (_) {
          continue;
        }
        try {
          if (
            value != null &&
            (typeof value === 'object' || typeof value === 'function') &&
            '_isMockFunction' in value &&
            this.isMockFunction(value) &&
            typeof value.mockClear === 'function'
          ) {
            value.mockClear();
          }
        } catch (_) {
          // ignore errors clearing individual mocks
        }
      }
    };
  }
}

class PatchedReactNativeEnv extends ReactNativeEnv {
  constructor(config, context) {
    super(config, context);
    // Patch the moduleMocker instance created by the parent with jest-mock@29
    patchModuleMocker(this.moduleMocker);
  }
}

module.exports = PatchedReactNativeEnv;
