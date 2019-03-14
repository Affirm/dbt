import unittest

from dbt.clients.jinja import get_template
from dbt.clients.jinja import BlockIterator, BlockTag

class TestJinja(unittest.TestCase):
    def test_do(self):
        s = '{% set my_dict = {} %}\n{% do my_dict.update(a=1) %}'

        template = get_template(s, {})
        mod = template.make_module()
        self.assertEqual(mod.my_dict, {'a': 1})


class TestBlockLexer(unittest.TestCase):
    def test_basic(self):
        body = '{{ config(foo="bar") }}\r\nselect * from this.that\r\n'
        block_data = '  \n\r\t{%- mytype foo %}'+body+'{%endmytype -%}'
        iterator = BlockIterator(block_data)
        blocks = iterator.lex_for_blocks()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type_name, 'mytype')
        self.assertEqual(blocks[0].block_name, 'foo')
        self.assertEqual(blocks[0].data, body)
        self.assertEqual(blocks[0].block_data, block_data)

    def test_multiple(self):
        body_one = '{{ config(foo="bar") }}\r\nselect * from this.that\r\n'
        body_two = (
            '{{ config(bar=1)}}\r\nselect * from {% if foo %} thing '
            '{% else %} other_thing {% endif %}'
        )

        block_data = (
            '  {% mytype foo %}' + body_one + '{% endmytype %}' +
            '\r\n{% othertype bar %}' + body_two + '{% endothertype %}'
        )
        iterator = BlockIterator(block_data)
        blocks = iterator.lex_for_blocks()
        self.assertEqual(len(blocks), 2)

    def test_comments(self):
        body = '{{ config(foo="bar") }}\r\nselect * from this.that\r\n'
        comment = '{# my comment #}'
        block_data = '  \n\r\t{%- mytype foo %}'+body+'{%endmytype -%}'
        iterator = BlockIterator(comment+block_data)
        blocks = iterator.lex_for_blocks()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type_name, 'mytype')
        self.assertEqual(blocks[0].block_name, 'foo')
        self.assertEqual(blocks[0].data, body)
        self.assertEqual(blocks[0].block_data, block_data)

    def test_evil_comments(self):
        body = '{{ config(foo="bar") }}\r\nselect * from this.that\r\n'
        comment = '{# external comment {% othertype bar %} select * from thing.other_thing{% endothertype %} #}'
        block_data = '  \n\r\t{%- mytype foo %}'+body+'{%endmytype -%}'
        iterator = BlockIterator(comment+block_data)
        blocks = iterator.lex_for_blocks()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type_name, 'mytype')
        self.assertEqual(blocks[0].block_name, 'foo')
        self.assertEqual(blocks[0].data, body)
        self.assertEqual(blocks[0].block_data, block_data)

    def test_nested_comments(self):
        body = '{# my comment #} {{ config(foo="bar") }}\r\nselect * from {# my other comment embedding {% endmytype %} #} this.that\r\n'
        block_data = '  \n\r\t{%- mytype foo %}'+body+'{% endmytype -%}'
        comment = '{# external comment {% othertype bar %} select * from thing.other_thing{% endothertype %} #}'
        # import ipdb;ipdb.set_trace()
        iterator = BlockIterator(comment+block_data)
        blocks = iterator.lex_for_blocks()
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0].block_type_name, 'mytype')
        self.assertEqual(blocks[0].block_name, 'foo')
        self.assertEqual(blocks[0].data, body)
        self.assertEqual(blocks[0].block_data, block_data)

    def test_complex_file(self):
        iterator = BlockIterator(complex_archive_file)
        blocks = iterator.lex_for_blocks()
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[0].block_type_name, 'mytype')
        self.assertEqual(blocks[0].block_name, 'foo')
        self.assertEqual(blocks[0].block_data, '{% mytype foo %} some stuff {% endmytype %}')
        self.assertEqual(blocks[0].data, ' some stuff ')
        self.assertEqual(blocks[1].block_type_name, 'mytype')
        self.assertEqual(blocks[1].block_name, 'bar')
        self.assertEqual(blocks[1].block_data, bar_block)
        self.assertEqual(blocks[1].data, bar_block[16:-15].rstrip())
        self.assertEqual(blocks[2].block_type_name, 'myothertype')
        self.assertEqual(blocks[2].block_name, 'x')
        self.assertEqual(blocks[2].block_data, x_block.strip())
        self.assertEqual(blocks[2].data, x_block[len('\n{% myothertype x %}'):-len('{% endmyothertype %}\n')])


bar_block = '''{% mytype bar %}
{# a comment
    that inside it has
    {% mytype baz %}
{% endmyothertype %}
{% endmytype %}
{% endmytype %}
    {#
{% endmytype %}#}

some other stuff

{%- endmytype%}'''

x_block = '''
{% myothertype x %}
before
{##}
and after
{% endmyothertype %}
'''

complex_archive_file = '''
{#some stuff {% mytype foo %} #}
{% mytype foo %} some stuff {% endmytype %}

'''+bar_block+x_block
