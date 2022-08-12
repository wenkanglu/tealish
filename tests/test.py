import unittest
from tealish import ParseError, compile_lines, minify_teal, TealishCompiler
import tealish


def compile_min(p):
    teal = compile_lines(p)
    min_teal, _ = minify_teal(teal)
    # remove 'pragma' line
    output = min_teal[1:]
    return output


class TestFields(unittest.TestCase):

    def test_group_index_0(self):
        teal = compile_min([
            'assert(Gtxn[0].TypeEnum)'
        ])
        self.assertEqual(teal[0], 'gtxn 0 TypeEnum')

    def test_group_index_1(self):
        teal = compile_min([
            'assert(Gtxn[1].TypeEnum)'
        ])
        self.assertEqual(teal[0], 'gtxn 1 TypeEnum')

    def test_group_index_15(self):
        teal = compile_min([
            'assert(Gtxn[15].TypeEnum)'
        ])
        self.assertEqual(teal[0], 'gtxn 15 TypeEnum')

    def test_group_index_negative(self):
        teal = compile_min([
            'assert(Gtxn[-1].TypeEnum)'
        ])
        self.assertListEqual(teal[:-1], ['txn GroupIndex', 'pushint 1', '-', 'gtxns TypeEnum'])

    def test_group_index_positive(self):
        teal = compile_min([
            'assert(Gtxn[+1].TypeEnum)'
        ])
        self.assertListEqual(teal[:-1], ['txn GroupIndex', 'pushint 1', '+', 'gtxns TypeEnum'])

    def test_group_index_var(self):
        teal = compile_min([
            'int index = 1',
            'assert(Gtxn[index].TypeEnum)'
        ])
        self.assertListEqual(teal[-3:-1], ['load 0 // index', 'gtxns TypeEnum'])

    def test_group_index_expression(self):
        teal = compile_min([
            'assert(Gtxn[1 + 2].TypeEnum)'
        ])
        self.assertListEqual(teal[:-1], ['pushint 1', 'pushint 2', '+', 'gtxns TypeEnum'])


class TestAssignment(unittest.TestCase):

    def test_assign(self):
        teal = compile_min([
            'int x = 1'
        ])
        self.assertListEqual(teal, ['pushint 1', 'store 0 // x'])

    def test_declare_assign(self):
        teal = compile_min([
            'int x',
            'x = 1'
        ])
        self.assertListEqual(teal, ['pushint 1', 'store 0 // x'])

    def test_double_assign(self):
        teal = compile_min([
            'int exists',
            'int balance',
            'exists, balance = asset_holding_get(AssetBalance, 0, 123)'
        ])
        self.assertListEqual(teal, ['pushint 0', 'pushint 123', 'asset_holding_get AssetBalance', 'store 0 // exists', 'store 1 // balance'])

    def test_fail_assign_without_declare(self):
        with self.assertRaises(tealish.CompileError) as e:
            teal = compile_min([
                'x = 1'
            ])
            print(teal)
        self.assertEqual(e.exception.args[0], 'Var "x" not declared in current scope at line 1')

    def test_fail_invalid(self):
        with self.assertRaises(ParseError):
            teal = compile_min([
                'int balanceexists, balance = asset_holding_get(AssetBalance, 0, 123)'
            ])
            print(teal)


class TestAssert(unittest.TestCase):

    def test_pass_assert_with_message(self):
        teal = compile_lines(['assert(1, "Error 1")'])
        self.assertListEqual(teal[2:], ['pushint 1', 'assert // Error 1'])

    def test_pass_assert_with_message_collection(self):
        compiler = TealishCompiler(['assert(0)', 'assert(1, "Error 1")'])
        teal = compiler.compile()
        self.assertDictEqual(compiler.error_messages, {2: 'Error 1'})

    def test_pass_simple_assert(self):
        teal = compile_lines(['assert(1)'])
        self.assertListEqual(teal[2:], ['pushint 1', 'assert'])

    def test_pass_assert_with_group_expression(self):
        teal = compile_lines(['assert(1 && (2 >= 1))'])

    def test_pass_1(self):
        teal = compile_lines(['int x = balance(0)'])
        self.assertListEqual(teal[2:], ['pushint 0', 'balance', 'store 0 // x'])


class TestFunctionReturn(unittest.TestCase):

    def test_pass(self):
        teal = compile_lines([
            'func f():',
            'return',
            'end',
        ])

    def test_fail_no_return(self):
        with self.assertRaises(ParseError) as e:
            compile_lines([
                'func f():',
                'assert(1)',
                'end',
            ])
        self.assertIn('func must end with a return statement', e.exception.args[0])

    def test_pass_return_literal(self):
        teal = compile_lines([
            'func f():',
            'return 1',
            'end',
        ])

    def test_pass_return_two_literals(self):
        teal = compile_lines([
            'func f():',
            'return 1, 2',
            'end',
        ])

    def test_pass_return_math_expression(self):
        teal = compile_lines([
            'func f():',
            'return 1 + 2',
            'end',
        ])

    def test_pass_return_two_math_expressions(self):
        teal = compile_lines([
            'func f():',
            'return 1 + 2, 3 + 1',
            'end',
        ])

    def test_pass_return_bytes_with_comma(self):
        teal = compile_min([
            'func f():',
            'return "1,2,3"',
            'end',
        ])
        self.assertListEqual(teal[1:], ['pushbytes "1,2,3"', 'retsub'])

    def test_pass_return_two_func_calls(self):
        teal = compile_min([
            'func f():',
            'return sqrt(25), exp(5, 2)',
            'end',
        ])
        self.assertListEqual(teal[1:], ['pushint 5', 'pushint 2', 'exp', 'pushint 25', 'sqrt', 'retsub'])