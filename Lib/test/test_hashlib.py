# Test hashlib module
#
# $Id$
#
#  Copyright (C) 2005-2010   Gregory P. Smith (greg@krypto.org)
#  Licensed to PSF under a Contributor Agreement.
#

import array
import hashlib
import itertools
import os
import sys
try:
    import threading
except ImportError:
    threading = None
import unittest
import warnings
from test import support
from test.support import _4G, bigmemtest

# Were we compiled --with-pydebug or with #define Py_DEBUG?
COMPILED_WITH_PYDEBUG = hasattr(sys, 'gettotalrefcount')


def hexstr(s):
    assert isinstance(s, bytes), repr(s)
    h = "0123456789abcdef"
    r = ''
    for i in s:
        r += h[(i >> 4) & 0xF] + h[i & 0xF]
    return r


class HashLibTestCase(unittest.TestCase):
    supported_hash_names = ( 'md5', 'MD5', 'sha1', 'SHA1',
                             'sha224', 'SHA224', 'sha256', 'SHA256',
                             'sha384', 'SHA384', 'sha512', 'SHA512',
                             'sha3_224', 'sha3_256', 'sha3_384',
                             'sha3_512', 'SHA3_224', 'SHA3_256',
                             'SHA3_384', 'SHA3_512' )

    # Issue #14693: fallback modules are always compiled under POSIX
    _warn_on_extension_import = os.name == 'posix' or COMPILED_WITH_PYDEBUG

    def _conditional_import_module(self, module_name):
        """Import a module and return a reference to it or None on failure."""
        try:
            exec('import '+module_name)
        except ImportError as error:
            if self._warn_on_extension_import:
                warnings.warn('Did a C extension fail to compile? %s' % error)
        return locals().get(module_name)

    def __init__(self, *args, **kwargs):
        algorithms = set()
        for algorithm in self.supported_hash_names:
            algorithms.add(algorithm.lower())
        self.constructors_to_test = {}
        for algorithm in algorithms:
            self.constructors_to_test[algorithm] = set()

        # For each algorithm, test the direct constructor and the use
        # of hashlib.new given the algorithm name.
        for algorithm, constructors in self.constructors_to_test.items():
            constructors.add(getattr(hashlib, algorithm))
            def _test_algorithm_via_hashlib_new(data=None, _alg=algorithm):
                if data is None:
                    return hashlib.new(_alg)
                return hashlib.new(_alg, data)
            constructors.add(_test_algorithm_via_hashlib_new)

        _hashlib = self._conditional_import_module('_hashlib')
        if _hashlib:
            # These two algorithms should always be present when this module
            # is compiled.  If not, something was compiled wrong.
            assert hasattr(_hashlib, 'openssl_md5')
            assert hasattr(_hashlib, 'openssl_sha1')
            for algorithm, constructors in self.constructors_to_test.items():
                constructor = getattr(_hashlib, 'openssl_'+algorithm, None)
                if constructor:
                    constructors.add(constructor)

        _md5 = self._conditional_import_module('_md5')
        if _md5:
            self.constructors_to_test['md5'].add(_md5.md5)
        _sha1 = self._conditional_import_module('_sha1')
        if _sha1:
            self.constructors_to_test['sha1'].add(_sha1.sha1)
        _sha256 = self._conditional_import_module('_sha256')
        if _sha256:
            self.constructors_to_test['sha224'].add(_sha256.sha224)
            self.constructors_to_test['sha256'].add(_sha256.sha256)
        _sha512 = self._conditional_import_module('_sha512')
        if _sha512:
            self.constructors_to_test['sha384'].add(_sha512.sha384)
            self.constructors_to_test['sha512'].add(_sha512.sha512)
        _sha3 = self._conditional_import_module('_sha3')
        if _sha3:
            self.constructors_to_test['sha3_224'].add(_sha3.sha3_224)
            self.constructors_to_test['sha3_256'].add(_sha3.sha3_256)
            self.constructors_to_test['sha3_384'].add(_sha3.sha3_384)
            self.constructors_to_test['sha3_512'].add(_sha3.sha3_512)

        super(HashLibTestCase, self).__init__(*args, **kwargs)

    def test_hash_array(self):
        a = array.array("b", range(10))
        constructors = self.constructors_to_test.values()
        for cons in itertools.chain.from_iterable(constructors):
            c = cons(a)
            c.hexdigest()

    def test_algorithms_guaranteed(self):
        self.assertEqual(hashlib.algorithms_guaranteed,
            set(_algo for _algo in self.supported_hash_names
                  if _algo.islower()))

    def test_algorithms_available(self):
        self.assertTrue(set(hashlib.algorithms_guaranteed).
                            issubset(hashlib.algorithms_available))

    def test_unknown_hash(self):
        self.assertRaises(ValueError, hashlib.new, 'spam spam spam spam spam')
        self.assertRaises(TypeError, hashlib.new, 1)

    def test_get_builtin_constructor(self):
        get_builtin_constructor = hashlib.__dict__[
                '__get_builtin_constructor']
        self.assertRaises(ValueError, get_builtin_constructor, 'test')
        try:
            import _md5
        except ImportError:
            pass
        # This forces an ImportError for "import _md5" statements
        sys.modules['_md5'] = None
        try:
            self.assertRaises(ValueError, get_builtin_constructor, 'md5')
        finally:
            if '_md5' in locals():
                sys.modules['_md5'] = _md5
            else:
                del sys.modules['_md5']
        self.assertRaises(TypeError, get_builtin_constructor, 3)

    def test_hexdigest(self):
        for name in self.supported_hash_names:
            h = hashlib.new(name)
            assert isinstance(h.digest(), bytes), name
            self.assertEqual(hexstr(h.digest()), h.hexdigest())


    def test_large_update(self):
        aas = b'a' * 128
        bees = b'b' * 127
        cees = b'c' * 126

        for name in self.supported_hash_names:
            m1 = hashlib.new(name)
            m1.update(aas)
            m1.update(bees)
            m1.update(cees)

            m2 = hashlib.new(name)
            m2.update(aas + bees + cees)
            self.assertEqual(m1.digest(), m2.digest())

    def check(self, name, data, digest):
        digest = digest.lower()
        constructors = self.constructors_to_test[name]
        # 2 is for hashlib.name(...) and hashlib.new(name, ...)
        self.assertGreaterEqual(len(constructors), 2)
        for hash_object_constructor in constructors:
            computed = hash_object_constructor(data).hexdigest()
            self.assertEqual(
                    computed, digest,
                    "Hash algorithm %s constructed using %s returned hexdigest"
                    " %r for %d byte input data that should have hashed to %r."
                    % (name, hash_object_constructor,
                       computed, len(data), digest))

    def check_no_unicode(self, algorithm_name):
        # Unicode objects are not allowed as input.
        constructors = self.constructors_to_test[algorithm_name]
        for hash_object_constructor in constructors:
            self.assertRaises(TypeError, hash_object_constructor, 'spam')

    def test_no_unicode(self):
        self.check_no_unicode('md5')
        self.check_no_unicode('sha1')
        self.check_no_unicode('sha224')
        self.check_no_unicode('sha256')
        self.check_no_unicode('sha384')
        self.check_no_unicode('sha512')
        self.check_no_unicode('sha3_224')
        self.check_no_unicode('sha3_256')
        self.check_no_unicode('sha3_384')
        self.check_no_unicode('sha3_512')

    def test_case_md5_0(self):
        self.check('md5', b'', 'd41d8cd98f00b204e9800998ecf8427e')

    def test_case_md5_1(self):
        self.check('md5', b'abc', '900150983cd24fb0d6963f7d28e17f72')

    def test_case_md5_2(self):
        self.check('md5',
                   b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
                   'd174ab98d277d9f5a5611c2c9f419d9f')

    @bigmemtest(size=_4G + 5, memuse=1)
    def test_case_md5_huge(self, size):
        if size == _4G + 5:
            try:
                self.check('md5', b'A'*size, 'c9af2dff37468ce5dfee8f2cfc0a9c6d')
            except OverflowError:
                pass # 32-bit arch

    @bigmemtest(size=_4G - 1, memuse=1)
    def test_case_md5_uintmax(self, size):
        if size == _4G - 1:
            try:
                self.check('md5', b'A'*size, '28138d306ff1b8281f1a9067e1a1a2b3')
            except OverflowError:
                pass # 32-bit arch

    # use the three examples from Federal Information Processing Standards
    # Publication 180-1, Secure Hash Standard,  1995 April 17
    # http://www.itl.nist.gov/div897/pubs/fip180-1.htm

    def test_case_sha1_0(self):
        self.check('sha1', b"",
                   "da39a3ee5e6b4b0d3255bfef95601890afd80709")

    def test_case_sha1_1(self):
        self.check('sha1', b"abc",
                   "a9993e364706816aba3e25717850c26c9cd0d89d")

    def test_case_sha1_2(self):
        self.check('sha1',
                   b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
                   "84983e441c3bd26ebaae4aa1f95129e5e54670f1")

    def test_case_sha1_3(self):
        self.check('sha1', b"a" * 1000000,
                   "34aa973cd4c4daa4f61eeb2bdbad27316534016f")


    # use the examples from Federal Information Processing Standards
    # Publication 180-2, Secure Hash Standard,  2002 August 1
    # http://csrc.nist.gov/publications/fips/fips180-2/fips180-2.pdf

    def test_case_sha224_0(self):
        self.check('sha224', b"",
          "d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f")

    def test_case_sha224_1(self):
        self.check('sha224', b"abc",
          "23097d223405d8228642a477bda255b32aadbce4bda0b3f7e36c9da7")

    def test_case_sha224_2(self):
        self.check('sha224',
          b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
          "75388b16512776cc5dba5da1fd890150b0c6455cb4f58b1952522525")

    def test_case_sha224_3(self):
        self.check('sha224', b"a" * 1000000,
          "20794655980c91d8bbb4c1ea97618a4bf03f42581948b2ee4ee7ad67")


    def test_case_sha256_0(self):
        self.check('sha256', b"",
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    def test_case_sha256_1(self):
        self.check('sha256', b"abc",
          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_case_sha256_2(self):
        self.check('sha256',
          b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
          "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1")

    def test_case_sha256_3(self):
        self.check('sha256', b"a" * 1000000,
          "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0")


    def test_case_sha384_0(self):
        self.check('sha384', b"",
          "38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da"+
          "274edebfe76f65fbd51ad2f14898b95b")

    def test_case_sha384_1(self):
        self.check('sha384', b"abc",
          "cb00753f45a35e8bb5a03d699ac65007272c32ab0eded1631a8b605a43ff5bed"+
          "8086072ba1e7cc2358baeca134c825a7")

    def test_case_sha384_2(self):
        self.check('sha384',
                   b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmn"+
                   b"hijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu",
          "09330c33f71147e83d192fc782cd1b4753111b173b3b05d22fa08086e3b0f712"+
          "fcc7c71a557e2db966c3e9fa91746039")

    def test_case_sha384_3(self):
        self.check('sha384', b"a" * 1000000,
          "9d0e1809716474cb086e834e310a4a1ced149e9c00f248527972cec5704c2a5b"+
          "07b8b3dc38ecc4ebae97ddd87f3d8985")


    def test_case_sha512_0(self):
        self.check('sha512', b"",
          "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce"+
          "47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e")

    def test_case_sha512_1(self):
        self.check('sha512', b"abc",
          "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"+
          "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f")

    def test_case_sha512_2(self):
        self.check('sha512',
                   b"abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmn"+
                   b"hijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu",
          "8e959b75dae313da8cf4f72814fc143f8f7779c6eb9f7fa17299aeadb6889018"+
          "501d289e4900f7e4331b99dec4b5433ac7d329eeb6dd26545e96e55b874be909")

    def test_case_sha512_3(self):
        self.check('sha512', b"a" * 1000000,
          "e718483d0ce769644e2e42c7bc15b4638e1f98b13b2044285632a803afa973eb"+
          "de0ff244877ea60a4cb0432ce577c31beb009c5c2c49aa2e4eadb217ad8cc09b")

    # SHA-3 family
    def test_case_sha3_224_0(self):
        self.check('sha3_224', b"",
          "F71837502BA8E10837BDD8D365ADB85591895602FC552B48B7390ABD")

    def test_case_sha3_224_1(self):
        self.check('sha3_224', bytes.fromhex("CC"),
          "A9CAB59EB40A10B246290F2D6086E32E3689FAF1D26B470C899F2802")

    def test_case_sha3_224_2(self):
        self.check('sha3_224', bytes.fromhex("41FB"),
          "615BA367AFDC35AAC397BC7EB5D58D106A734B24986D5D978FEFD62C")

    def test_case_sha3_224_3(self):
        self.check('sha3_224', bytes.fromhex(
            "433C5303131624C0021D868A30825475E8D0BD3052A022180398F4CA4423B9"+
            "8214B6BEAAC21C8807A2C33F8C93BD42B092CC1B06CEDF3224D5ED1EC29784"+
            "444F22E08A55AA58542B524B02CD3D5D5F6907AFE71C5D7462224A3F9D9E53"+
            "E7E0846DCBB4CE"),
          "62B10F1B6236EBC2DA72957742A8D4E48E213B5F8934604BFD4D2C3A")

    @bigmemtest(size=_4G + 5, memuse=1)
    def test_case_sha3_224_huge(self, size):
        if size == _4G + 5:
            try:
                self.check('sha3_224', b'A'*size,
                           '58ef60057c9dddb6a87477e9ace5a26f0d9db01881cf9b10a9f8c224')
            except OverflowError:
                pass # 32-bit arch


    def test_case_sha3_256_0(self):
        self.check('sha3_256', b"",
          "C5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470")

    def test_case_sha3_256_1(self):
        self.check('sha3_256', bytes.fromhex("CC"),
          "EEAD6DBFC7340A56CAEDC044696A168870549A6A7F6F56961E84A54BD9970B8A")

    def test_case_sha3_256_2(self):
        self.check('sha3_256', bytes.fromhex("41FB"),
          "A8EACEDA4D47B3281A795AD9E1EA2122B407BAF9AABCB9E18B5717B7873537D2")

    def test_case_sha3_256_3(self):
        self.check('sha3_256', bytes.fromhex(
            "433C5303131624C0021D868A30825475E8D0BD3052A022180398F4CA4423B9"+
            "8214B6BEAAC21C8807A2C33F8C93BD42B092CC1B06CEDF3224D5ED1EC29784"+
            "444F22E08A55AA58542B524B02CD3D5D5F6907AFE71C5D7462224A3F9D9E53"+
            "E7E0846DCBB4CE"),
          "CE87A5173BFFD92399221658F801D45C294D9006EE9F3F9D419C8D427748DC41")


    def test_case_sha3_384_0(self):
        self.check('sha3_384', b"",
          "2C23146A63A29ACF99E73B88F8C24EAA7DC60AA771780CCC006AFBFA8FE2479B"+
          "2DD2B21362337441AC12B515911957FF")

    def test_case_sha3_384_1(self):
        self.check('sha3_384', bytes.fromhex("CC"),
          "1B84E62A46E5A201861754AF5DC95C4A1A69CAF4A796AE405680161E29572641"+
          "F5FA1E8641D7958336EE7B11C58F73E9")

    def test_case_sha3_384_2(self):
        self.check('sha3_384', bytes.fromhex("41FB"),
          "495CCE2714CD72C8C53C3363D22C58B55960FE26BE0BF3BBC7A3316DD563AD1D"+
          "B8410E75EEFEA655E39D4670EC0B1792")

    def test_case_sha3_384_3(self):
        self.check('sha3_384', bytes.fromhex(
            "433C5303131624C0021D868A30825475E8D0BD3052A022180398F4CA4423B9"+
            "8214B6BEAAC21C8807A2C33F8C93BD42B092CC1B06CEDF3224D5ED1EC29784"+
            "444F22E08A55AA58542B524B02CD3D5D5F6907AFE71C5D7462224A3F9D9E53"+
            "E7E0846DCBB4CE"),
          "135114508DD63E279E709C26F7817C0482766CDE49132E3EDF2EEDD8996F4E35"+
          "96D184100B384868249F1D8B8FDAA2C9")


    def test_case_sha3_512_0(self):
        self.check('sha3_512', b"",
          "0EAB42DE4C3CEB9235FC91ACFFE746B29C29A8C366B7C60E4E67C466F36A4304"+
          "C00FA9CAF9D87976BA469BCBE06713B435F091EF2769FB160CDAB33D3670680E")

    def test_case_sha3_512_1(self):
        self.check('sha3_512', bytes.fromhex("CC"),
          "8630C13CBD066EA74BBE7FE468FEC1DEE10EDC1254FB4C1B7C5FD69B646E4416"+
          "0B8CE01D05A0908CA790DFB080F4B513BC3B6225ECE7A810371441A5AC666EB9")

    def test_case_sha3_512_2(self):
        self.check('sha3_512', bytes.fromhex("41FB"),
          "551DA6236F8B96FCE9F97F1190E901324F0B45E06DBBB5CDB8355D6ED1DC34B3"+
          "F0EAE7DCB68622FF232FA3CECE0D4616CDEB3931F93803662A28DF1CD535B731")

    def test_case_sha3_512_3(self):
        self.check('sha3_512', bytes.fromhex(
            "433C5303131624C0021D868A30825475E8D0BD3052A022180398F4CA4423B9"+
            "8214B6BEAAC21C8807A2C33F8C93BD42B092CC1B06CEDF3224D5ED1EC29784"+
            "444F22E08A55AA58542B524B02CD3D5D5F6907AFE71C5D7462224A3F9D9E53"+
            "E7E0846DCBB4CE"),
          "527D28E341E6B14F4684ADB4B824C496C6482E51149565D3D17226828884306B"+
          "51D6148A72622C2B75F5D3510B799D8BDC03EAEDE453676A6EC8FE03A1AD0EAB")


    def test_gil(self):
        # Check things work fine with an input larger than the size required
        # for multithreaded operation (which is hardwired to 2048).
        gil_minsize = 2048

        for name in self.supported_hash_names:
            m = hashlib.new(name)
            m.update(b'1')
            m.update(b'#' * gil_minsize)
            m.update(b'1')

            m = hashlib.new(name, b'x' * gil_minsize)
            m.update(b'1')

        m = hashlib.md5()
        m.update(b'1')
        m.update(b'#' * gil_minsize)
        m.update(b'1')
        self.assertEqual(m.hexdigest(), 'cb1e1a2cbc80be75e19935d621fb9b21')

        m = hashlib.md5(b'x' * gil_minsize)
        self.assertEqual(m.hexdigest(), 'cfb767f225d58469c5de3632a8803958')

    @unittest.skipUnless(threading, 'Threading required for this test.')
    @support.reap_threads
    def test_threaded_hashing(self):
        # Updating the same hash object from several threads at once
        # using data chunk sizes containing the same byte sequences.
        #
        # If the internal locks are working to prevent multiple
        # updates on the same object from running at once, the resulting
        # hash will be the same as doing it single threaded upfront.
        hasher = hashlib.sha1()
        num_threads = 5
        smallest_data = b'swineflu'
        data = smallest_data*200000
        expected_hash = hashlib.sha1(data*num_threads).hexdigest()

        def hash_in_chunks(chunk_size, event):
            index = 0
            while index < len(data):
                hasher.update(data[index:index+chunk_size])
                index += chunk_size
            event.set()

        events = []
        for threadnum in range(num_threads):
            chunk_size = len(data) // (10**threadnum)
            assert chunk_size > 0
            assert chunk_size % len(smallest_data) == 0
            event = threading.Event()
            events.append(event)
            threading.Thread(target=hash_in_chunks,
                             args=(chunk_size, event)).start()

        for event in events:
            event.wait()

        self.assertEqual(expected_hash, hasher.hexdigest())

def test_main():
    support.run_unittest(HashLibTestCase)

if __name__ == "__main__":
    test_main()
