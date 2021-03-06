from test.integration.base import DBTIntegrationTest, use_profile

from dbt import deprecations
import dbt.exceptions


class TestDeprecations(DBTIntegrationTest):
    def setUp(self):
        super(TestDeprecations, self).setUp()
        deprecations.reset_deprecations()

    @property
    def schema(self):
        return "deprecation_test_012"

    @staticmethod
    def dir(path):
        return "test/integration/012_deprecation_tests/" + path.lstrip("/")

    @property
    def models(self):
        return self.dir("models")

    @use_profile('postgres')
    def test_postgres_deprecations_fail(self):
        with self.assertRaises(dbt.exceptions.CompilationException):
            self.run_dbt(strict=True)

    @use_profile('postgres')
    def test_postgres_deprecations(self):
        self.assertEqual(deprecations.active_deprecations, set())
        results = self.run_dbt(strict=False)
        self.assertEqual({'adapter:already_exists', 'sql_where'},
                         deprecations.active_deprecations)
