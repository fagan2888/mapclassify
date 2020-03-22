import numpy as np
import unittest
import types
from ..classifiers import *
from ..classifiers import binC, bin, bin1d, load_example
from ..pooling import Pooled


RTOL = 0.0001


class TestQuantile(unittest.TestCase):
    def test_quantile(self):
        y = np.arange(1000)
        expected = np.array([333.0, 666.0, 999.0])
        np.testing.assert_almost_equal(expected, quantile(y, k=3))

    def test_quantile_k4(self):
        x = np.arange(1000)
        qx = quantile(x, k=4)
        expected = np.array([249.75, 499.5, 749.25, 999.0])
        np.testing.assert_array_almost_equal(expected, qx)

    def test_quantile_k(self):
        y = np.random.random(1000)
        for k in range(5, 10):
            np.testing.assert_almost_equal(k, len(quantile(y, k)))
            self.assertEqual(k, len(quantile(y, k)))


class TestUpdate(unittest.TestCase):
    def setUp(self):
        np.random.seed(4414)
        self.data = np.random.normal(0, 10, size=10)
        self.new_data = np.random.normal(0, 10, size=4)

    def test_update(self):
        # Quantiles
        quants = Quantiles(self.data, k=3)
        known_yb = np.array([0, 1, 0, 1, 0, 2, 0, 2, 1, 2])
        np.testing.assert_allclose(quants.yb, known_yb, rtol=RTOL)
        new_yb = quants.update(self.new_data, k=4).yb
        known_new_yb = np.array([0, 3, 1, 0, 1, 2, 0, 2, 1, 3, 0, 3, 2, 3])
        np.testing.assert_allclose(new_yb, known_new_yb, rtol=RTOL)

        # User-Defined
        ud = UserDefined(self.data, [-20, 0, 5, 20])
        known_yb = np.array([1, 2, 1, 1, 1, 2, 0, 2, 1, 3])
        np.testing.assert_allclose(ud.yb, known_yb, rtol=RTOL)
        new_yb = ud.update(self.new_data).yb
        known_new_yb = np.array([1, 3, 1, 1, 1, 2, 1, 1, 1, 2, 0, 2, 1, 3])
        np.testing.assert_allclose(new_yb, known_new_yb, rtol=RTOL)

        # Fisher-Jenks Sampled
        fjs = FisherJenksSampled(self.data, k=3, pct=70)
        known_yb = np.array([1, 2, 0, 1, 1, 2, 0, 2, 1, 2])
        np.testing.assert_allclose(known_yb, fjs.yb, rtol=RTOL)
        new_yb = fjs.update(self.new_data, k=2).yb
        known_new_yb = np.array([0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1])
        np.testing.assert_allclose(known_new_yb, new_yb, rtol=RTOL)


class TestFindBin(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_find_bin(self):
        toclass = [0, 1, 3, 5, 50, 70, 101, 202, 390, 505, 800, 5000, 5001]
        mc = FisherJenks(self.V, k=5)
        known = [0, 0, 0, 0, 0, 0, 1, 2, 3, 3, 4, 4, 4]
        np.testing.assert_array_equal(known, mc.find_bin(toclass))
        mc2 = FisherJenks(self.V, k=9)
        known = [0, 0, 0, 0, 2, 2, 3, 5, 7, 7, 8, 8, 8]
        np.testing.assert_array_equal(known, mc2.find_bin(toclass))


class TestMake(unittest.TestCase):
    def setUp(self):
        self.data = [
            np.linspace(-5, 5, num=5),
            np.linspace(-10, 10, num=5),
            np.linspace(-20, 20, num=5),
        ]
        self.ei = EqualInterval.make()
        self.q5r = Quantiles.make(k=5, rolling=True)

    def test_make(self):
        self.assertIsInstance(self.ei, types.FunctionType)
        self.assertIsInstance(self.q5r, types.FunctionType)

        assert hasattr(self.ei, "_options")
        self.assertEqual(self.ei._options, dict())
        assert hasattr(self.q5r, "_options")
        self.assertEqual(self.q5r._options, {"k": 5, "rolling": True})

    def test_apply(self):
        ei_classes = [self.ei(d) for d in self.data]
        known = [np.arange(0, 5, 1)] * 3
        np.testing.assert_allclose(known, ei_classes)

        q5r_classes = [self.q5r(d) for d in self.data]
        known = [[0, 1, 2, 3, 4], [0, 0, 2, 3, 4], [0, 0, 2, 4, 4]]
        accreted_data = set(self.q5r.__defaults__[0].y)
        all_data = set(np.asarray(self.data).flatten())
        self.assertEqual(accreted_data, all_data)
        np.testing.assert_allclose(known, q5r_classes)


class TestBinC(unittest.TestCase):
    def test_bin_c(self):
        bins = list(range(2, 8))
        y = np.array(
            [
                [7, 5, 6],
                [2, 3, 5],
                [7, 2, 2],
                [3, 6, 7],
                [6, 3, 4],
                [6, 7, 4],
                [6, 5, 6],
                [4, 6, 7],
                [4, 6, 3],
                [3, 2, 7],
            ]
        )

        expected = np.array(
            [
                [5, 3, 4],
                [0, 1, 3],
                [5, 0, 0],
                [1, 4, 5],
                [4, 1, 2],
                [4, 5, 2],
                [4, 3, 4],
                [2, 4, 5],
                [2, 4, 1],
                [1, 0, 5],
            ]
        )
        np.testing.assert_array_equal(expected, binC(y, bins))


class TestBin(unittest.TestCase):
    def test_bin(self):
        y = np.array(
            [
                [7, 13, 14],
                [10, 11, 13],
                [7, 17, 2],
                [18, 3, 14],
                [9, 15, 8],
                [7, 13, 12],
                [16, 6, 11],
                [19, 2, 15],
                [11, 11, 9],
                [3, 2, 19],
            ]
        )
        bins = [10, 15, 20]
        expected = np.array(
            [
                [0, 1, 1],
                [0, 1, 1],
                [0, 2, 0],
                [2, 0, 1],
                [0, 1, 0],
                [0, 1, 1],
                [2, 0, 1],
                [2, 0, 1],
                [1, 1, 0],
                [0, 0, 2],
            ]
        )

        np.testing.assert_array_equal(expected, bin(y, bins))


class TestBin1d(unittest.TestCase):
    def test_bin1d(self):
        y = np.arange(100, dtype="float")
        bins = [25, 74, 100]
        binIds = np.array(
            [
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
                2,
            ]
        )
        counts = np.array([26, 49, 25])

        np.testing.assert_array_equal(binIds, bin1d(y, bins)[0])
        np.testing.assert_array_equal(counts, bin1d(y, bins)[1])


class TestNaturalBreaks(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_natural_breaks(self):
        # self.assertEqual(expected, natural_breaks(values, k, itmax))
        assert True  # TODO: implement your test here

    def test_NaturalBreaks(self):
        nb = NaturalBreaks(self.V, 5)
        self.assertEqual(nb.k, 5)
        self.assertEqual(len(nb.counts), 5)
        np.testing.assert_array_almost_equal(nb.counts, np.array([49, 3, 4, 1, 1]))

    def test_NaturalBreaks_stability(self):
        for i in range(10):
            nb = NaturalBreaks(self.V, 5)
            self.assertEqual(nb.k, 5)
            self.assertEqual(len(nb.counts), 5)

    def test_NaturalBreaks_randomData(self):
        for i in range(10):
            V = np.random.random(50) * (i + 1)
            nb = NaturalBreaks(V, 5)
            self.assertEqual(nb.k, 5)
            self.assertEqual(len(nb.counts), 5)


class TestHeadTailBreaks(unittest.TestCase):
    def setUp(self):
        x = list(range(1, 1000))
        y = []
        for i in x:
            y.append(i ** (-2))
        self.V = np.array(y)

    def test_HeadTailBreaks(self):
        htb = HeadTailBreaks(self.V)
        self.assertEqual(htb.k, 4)
        self.assertEqual(len(htb.counts), 4)
        np.testing.assert_array_almost_equal(htb.counts, np.array([975, 21, 2, 1]))

    def test_HeadTailBreaks_doublemax(self):
        V = np.append(self.V, self.V.max())
        htb = HeadTailBreaks(V)
        self.assertEqual(htb.k, 4)
        self.assertEqual(len(htb.counts), 4)
        np.testing.assert_array_almost_equal(htb.counts, np.array([980, 17, 1, 2]))


class TestMapClassifier(unittest.TestCase):
    def test_Map_Classifier(self):
        # map__classifier = Map_Classifier(y)
        assert True  # TODO: implement your test here

    def test___repr__(self):
        # map__classifier = Map_Classifier(y)
        # self.assertEqual(expected, map__classifier.__repr__())
        assert True  # TODO: implement your test here

    def test___str__(self):
        # map__classifier = Map_Classifier(y)
        # self.assertEqual(expected, map__classifier.__str__())
        assert True  # TODO: implement your test here

    def test_get_adcm(self):
        # map__classifier = Map_Classifier(y)
        # self.assertEqual(expected, map__classifier.get_adcm())
        assert True  # TODO: implement your test here

    def test_get_gadf(self):
        # map__classifier = Map_Classifier(y)
        # self.assertEqual(expected, map__classifier.get_gadf())
        assert True  # TODO: implement your test here

    def test_get_tss(self):
        # map__classifier = Map_Classifier(y)
        # self.assertEqual(expected, map__classifier.get_tss())
        assert True  # TODO: implement your test here


class TestEqualInterval(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_EqualInterval(self):
        ei = EqualInterval(self.V)
        np.testing.assert_array_almost_equal(ei.counts, np.array([57, 0, 0, 0, 1]))
        np.testing.assert_array_almost_equal(
            ei.bins, np.array([822.394, 1644.658, 2466.922, 3289.186, 4111.45])
        )


class TestPercentiles(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_Percentiles(self):
        pc = Percentiles(self.V)
        np.testing.assert_array_almost_equal(
            pc.bins,
            np.array(
                [
                    1.35700000e-01,
                    5.53000000e-01,
                    9.36500000e00,
                    2.13914000e02,
                    2.17994800e03,
                    4.11145000e03,
                ]
            ),
        )
        np.testing.assert_array_almost_equal(pc.counts, np.array([1, 5, 23, 23, 5, 1]))


class TestBoxPlot(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_BoxPlot(self):
        bp = BoxPlot(self.V)
        bins = np.array(
            [
                -5.28762500e01,
                2.56750000e00,
                9.36500000e00,
                3.95300000e01,
                9.49737500e01,
                4.11145000e03,
            ]
        )
        np.testing.assert_array_almost_equal(bp.bins, bins)


class TestQuantiles(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_Quantiles(self):
        q = Quantiles(self.V, k=5)
        np.testing.assert_array_almost_equal(
            q.bins,
            np.array(
                [
                    1.46400000e00,
                    5.79800000e00,
                    1.32780000e01,
                    5.46160000e01,
                    4.11145000e03,
                ]
            ),
        )
        np.testing.assert_array_almost_equal(q.counts, np.array([12, 11, 12, 11, 12]))


class TestStdMean(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_StdMean(self):
        s = StdMean(self.V)
        np.testing.assert_array_almost_equal(
            s.bins,
            np.array(
                [-967.36235382, -420.71712519, 672.57333208, 1219.21856072, 4111.45]
            ),
        )
        np.testing.assert_array_almost_equal(s.counts, np.array([0, 0, 56, 1, 1]))


class TestMaximumBreaks(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_MaximumBreaks(self):
        mb = MaximumBreaks(self.V, k=5)
        self.assertEqual(mb.k, 5)
        np.testing.assert_array_almost_equal(
            mb.bins, np.array([146.005, 228.49, 546.675, 2417.15, 4111.45])
        )
        np.testing.assert_array_almost_equal(mb.counts, np.array([50, 2, 4, 1, 1]))


class TestFisherJenks(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_FisherJenks(self):
        fj = FisherJenks(self.V)
        self.assertEqual(fj.adcm, 799.24000000000001)
        np.testing.assert_array_almost_equal(
            fj.bins, np.array([75.29, 192.05, 370.5, 722.85, 4111.45])
        )
        np.testing.assert_array_almost_equal(fj.counts, np.array([49, 3, 4, 1, 1]))


class TestJenksCaspall(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_JenksCaspall(self):
        np.random.seed(10)
        jc = JenksCaspall(self.V, k=5)
        np.testing.assert_array_almost_equal(jc.counts, np.array([14, 13, 14, 10, 7]))
        np.testing.assert_array_almost_equal(
            jc.bins,
            np.array(
                [
                    1.81000000e00,
                    7.60000000e00,
                    2.98200000e01,
                    1.81270000e02,
                    4.11145000e03,
                ]
            ),
        )


class TestJenksCaspallSampled(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_JenksCaspallSampled(self):
        np.random.seed(100)
        x = np.random.random(100000)
        jc = JenksCaspall(x)
        jcs = JenksCaspallSampled(x)
        np.testing.assert_array_almost_equal(
            jc.bins,
            np.array([0.19718393, 0.39655886, 0.59648522, 0.79780763, 0.99997979]),
        )
        np.testing.assert_array_almost_equal(
            jcs.bins,
            np.array([0.20856569, 0.41513931, 0.62457691, 0.82561423, 0.99997979]),
        )


class TestJenksCaspallForced(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_JenksCaspallForced(self):
        np.random.seed(100)
        jcf = JenksCaspallForced(self.V, k=5)
        np.testing.assert_array_almost_equal(
            jcf.bins,
            np.array([1.34000000e00, 5.90000000e00, 1.67000000e01, 5.06500000e01, 4.11145000e03])
        )
        np.testing.assert_array_almost_equal(jcf.counts, np.array([12, 12, 13, 9, 12]))


class TestUserDefined(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_UserDefined(self):
        bins = [20, max(self.V)]
        ud = UserDefined(self.V, bins)
        np.testing.assert_array_almost_equal(ud.bins, np.array([20.0, 4111.45]))
        np.testing.assert_array_almost_equal(ud.counts, np.array([37, 21]))

    def test_UserDefined_max(self):
        bins = np.array([20, 30])
        ud = UserDefined(self.V, bins)
        np.testing.assert_array_almost_equal(ud.bins, np.array([20.0, 30., 4111.45]))
        np.testing.assert_array_almost_equal(ud.counts, np.array([37, 4, 17]))


class TestMaxP(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_MaxP(self):
        np.random.seed(100)
        mp = MaxP(self.V)
        np.testing.assert_array_almost_equal(
            mp.bins,
            np.array(
                [
                    8.6999999999999993,
                    16.699999999999999,
                    20.469999999999999,
                    66.260000000000005,
                    4111.4499999999998,
                ]
            ),
        )
        np.testing.assert_array_almost_equal(mp.counts, np.array([29, 8, 1, 10, 10]))


class TestGadf(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_gadf(self):
        qgadf = gadf(self.V)
        self.assertEqual(qgadf[0], 15)
        self.assertEqual(qgadf[-1], 0.37402575909092828)


class TestKClassifiers(unittest.TestCase):
    def setUp(self):
        self.V = load_example()

    def test_K_classifiers(self):
        np.random.seed(100)
        ks = KClassifiers(self.V)
        self.assertEqual(ks.best.name, "FisherJenks")
        self.assertEqual(ks.best.gadf, 0.84810327199081048)
        self.assertEqual(ks.best.k, 4)

class TestPooled(unittest.TestCase):
    def setUp(self):
        n = 20
        self.data = np.array([np.arange(n)+i*n for i in range(1, 4)]).T

    def test_pooled(self):
        res = Pooled(self.data, k=4)
        self.assertEqual(res.k, 4)
        np.testing.assert_array_almost_equal(res.col_classifiers[0].counts,
                                             np.array([15,  5,  0,  0]))
        np.testing.assert_array_almost_equal(res.col_classifiers[-1].counts,
                                             np.array([  0,  0, 5,  15]))
        np.testing.assert_array_almost_equal(res.global_classifier.counts,
                                             np.array([15,  15,  15,  15]))
        res = Pooled(self.data, classifier='BoxPlot', hinge=1.5)
        np.testing.assert_array_almost_equal(res.col_classifiers[0].bins,
                                             np.array([ -9.5 ,  34.75,  49.5 ,  64.25, 108.5 ]))

if __name__ == "__main__":
    unittest.main()
