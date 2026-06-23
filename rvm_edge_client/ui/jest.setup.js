/**
 * Jest setup shim: adds clearMocksOnScope to jest-mock@29's ModuleMocker prototype.
 * Required because react-native pulls in jest-environment-node@29 (jest-mock@29)
 * which lacks this method introduced in jest-mock@30.
 */
const jestMock = require('jest-mock');

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
