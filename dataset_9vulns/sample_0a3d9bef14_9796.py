#!/usr/bin/python
#
# Copyright (c) 2012 The Native Client Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#

"""
Responsible for generating the testing decoders based on
parsed table representations.
"""

import dgen_core
import dgen_opt
import dgen_output
import dgen_decoder
import dgen_actuals
import dgen_baselines
import os
import pickle
import subprocess

_cl_args = {}

CLASS = '%(DECODER)s_%(rule)s'
NAMED_CLASS = 'Named%(DECODER)s_%(rule)s'
INSTANCE = '%(DECODER_class)s_instance_'
BASE_TESTER='%(decoder_base)sTester%(base_test_case)s'
BASE_BASE_TESTER='%(decoder_base)sTester%(qualifier)s'
DECODER_TESTER='%(baseline)sTester_%(test_case)s'

def _safety_to_check(safety):
  return [s for s in safety if not isinstance(s, str)]

def _interesting_patterns(patterns):
  return [ p for p in patterns if (
      (not p.column or p.column.name() != '$pattern')
      and not p.matches_any())]

def _install_action(decoder, action, values):
  values['baseline'] = action.baseline()
  values['actual'] = action.actual()
  values['decoder_base'] = decoder.base_class(values['baseline'])
  values['rule'] = action.rule()
  values['qualifier'] = ''.join([s for s in action.safety()
                                 if isinstance(s, str)])
  if action.constraints():
    values['qualifier'] += (action.constraints().other
                            if action.constraints().other else '')
  else:
    values['qualifier'] =''
  values['pattern'] = action.pattern()
  for field in [ 'base_test_case', 'test_case', 'test_pattern' ]:
    if not values.get(field):
      values[field] = ''
  values['baseline_class'] =  _decoder_replace(CLASS, 'baseline') % values
  values['actual_class'] = _decoder_replace(CLASS, 'actual') % values
  _install_baseline_and_actuals('named_DECODER_class', NAMED_CLASS, values)
  _install_baseline_and_actuals('DECODER_instance', INSTANCE, values)
  values['base_tester'] = BASE_TESTER % values
  values['base_base_tester'] = BASE_BASE_TESTER % values
  values['decoder_tester'] = DECODER_TESTER % values

def _decoder_replace(string, basis):
  return string.replace('DECODER', basis)

def _install_key_pattern(key, pattern, basis, values):
  values[_decoder_replace(key, basis)] = (
      _decoder_replace(pattern, basis) % values)

def _install_baseline_and_actuals(key, pattern, values):
  for basis in ['baseline', 'actual']:
    _install_key_pattern(key, pattern, basis, values)

def _generate_baseline_and_actual(code, symbol, decoder,
                                  values, out, actions=['rule']):
  generated_symbols = set()

  baseline_actions = actions[:]
  baseline_actions.insert(0, 'baseline');
  baseline_code = _decoder_replace(code, 'baseline')
  baseline_symbol = _decoder_replace(symbol, 'baseline');
  for d in decoder.action_filter(baseline_actions).decoders():
    _install_action(decoder, d, values);
    sym_name = (baseline_symbol % values)
    if sym_name not in generated_symbols:
      out.write(baseline_code % values)
      generated_symbols.add(sym_name)

  actual_actions = actions[:]
  actual_actions.insert(0, 'actual-not-baseline')
  actual_code = _decoder_replace(code, 'actual')
  actual_symbol = _decoder_replace(symbol, 'actual')
  for d in decoder.action_filter(actual_actions).decoders():
    if d.actual():
      _install_action(decoder, d, values);
      sym_name = (actual_symbol % values)
      if sym_name not in generated_symbols:
        out.write(actual_code % values)
        generated_symbols.add(sym_name)

NAMED_BASES_H_HEADER="""%(FILE_HEADER)s
%(NOT_TCB_MESSAGE)s

#ifndef %(IFDEF_NAME)s
#define %(IFDEF_NAME)s

#include "native_client/src/trusted/validator_arm/actual_classes.h"
#include "native_client/src/trusted/validator_arm/baseline_classes.h"
#include "native_client/src/trusted/validator_arm/named_class_decoder.h"
#include "%(FILENAME_BASE)s_baselines.h"

namespace nacl_arm_test {
"""

GENERATED_BASELINE_HEADER="""
/*
 * Define named class decoders for each automatically generated baseline
 * decoder.
 */
"""

NAMED_GEN_BASE_DECLARE="""class Named%(gen_base)s
    : public NamedClassDecoder {
 public:
  Named%(gen_base)s()
    : NamedClassDecoder(decoder_, "%(gen_base)s")
  {}

 private:
  nacl_arm_dec::%(gen_base)s decoder_;
  NACL_DISALLOW_COPY_AND_ASSIGN(Named%(gen_base)s);
};

"""

NAMED_BASES_H_FOOTER="""
} // namespace nacl_arm_test
#endif  // %(IFDEF_NAME)s
"""

NAMED_BASES_H_SUFFIX = '_named_bases.h'

def generate_named_bases_h(decoder, decoder_name, filename, out, cl_args):
  global _cl_args
  if not decoder.primary: raise Exception('No tables provided.')
  assert filename.endswith(NAMED_BASES_H_SUFFIX)
  _cl_args = cl_args

  decoder = dgen_baselines.AddBaselinesToDecoder(decoder)

  values = {
      'FILE_HEADER': dgen_output.HEADER_BOILERPLATE,
      'NOT_TCB_MESSAGE' : dgen_output.NOT_TCB_BOILERPLATE,
      'IFDEF_NAME' : dgen_output.ifdef_name(filename),
      'FILENAME_BASE': filename[:-len(NAMED_BASES_H_SUFFIX)],
      'decoder_name': decoder_name,
      }
  out.write(NAMED_BASES_H_HEADER % values)
  _generate_generated_baseline(decoder, out)
  out.write(NAMED_BASES_H_FOOTER % values)

def _generate_generated_baseline(decoder, out):
  generated_symbols = set()
  values = {}
  out.write(GENERATED_BASELINE_HEADER % values)
  for d in decoder.action_filter(['generated_baseline']).decoders():
    gen_base = d.find('generated_baseline')
    if gen_base and gen_base not in generated_symbols:
      values['gen_base'] = gen_base
      out.write(NAMED_GEN_BASE_DECLARE % values)
      generated_symbols.add(gen_base)

NAMED_CLASSES_H_HEADER="""%(FILE_HEADER)s
%(NOT_TCB_MESSAGE)s

#ifndef %(IFDEF_NAME)s
#define %(IFDEF_NAME)s

#include "native_client/src/trusted/validator_arm/actual_classes.h"
#include "native_client/src/trusted/validator_arm/baseline_classes.h"
#include "native_client/src/trusted/validator_arm/named_class_decoder.h"
#include "%(FILENAME_BASE)s_actuals.h"

#include "%(FILENAME_BASE)s_named_bases.h"
"""

RULE_CLASSES_HEADER="""
/*
 * Define rule decoder classes.
 */
namespace nacl_arm_dec {

"""

RULE_CLASS="""class %(DECODER_class)s
    : public %(DECODER)s {
};

"""

RULE_CLASS_SYM="%(DECODER_class)s"

NAMED_DECODERS_HEADER="""}  // nacl_arm_dec

namespace nacl_arm_test {

/*
 * Define named class decoders for each class decoder.
 * The main purpose of these classes is to introduce
 * instances that are named specifically to the class decoder
 * and/or rule that was used to parse them. This makes testing
 * much easier in that error messages use these named classes
 * to clarify what row in the corresponding table was used
 * to select this decoder. Without these names, debugging the
 * output of the test code would be nearly impossible
 */

"""

NAMED_CLASS_DECLARE="""class %(named_DECODER_class)s
    : public NamedClassDecoder {
 public:
  %(named_DECODER_class)s()
    : NamedClassDecoder(decoder_, "%(DECODER)s %(rule)s")
  {}

 private:
  nacl_arm_dec::%(DECODER_class)s decoder_;
  NACL_DISALLOW_COPY_AND_ASSIGN(%(named_DECODER_class)s);
};

"""

NAMED_CLASS_DECLARE_SYM="%(named_DECODER_class)s"

NAMED_CLASSES_H_FOOTER="""
// Defines the default parse action if the table doesn't define
// an action.
class NotImplementedNamed : public NamedClassDecoder {
 public:
  NotImplementedNamed()
    : NamedClassDecoder(decoder_, "not implemented")
  {}

 private:
  nacl_arm_dec::NotImplemented decoder_;
  NACL_DISALLOW_COPY_AND_ASSIGN(NotImplementedNamed);
};

} // namespace nacl_arm_test
#endif  // %(IFDEF_NAME)s
"""

def generate_named_classes_h(decoder, decoder_name, filename, out, cl_args):
  global _cl_args
  if not decoder.primary: raise Exception('No tables provided.')
  assert filename.endswith('_named_classes.h')
  _cl_args = cl_args

  actuals = cl_args.get('auto-actual')
  if actuals:
    decoder = dgen_actuals.AddAutoActualsToDecoder(decoder, actuals)

  values = {
      'FILE_HEADER': dgen_output.HEADER_BOILERPLATE,
      'NOT_TCB_MESSAGE' : dgen_output.NOT_TCB_BOILERPLATE,
      'IFDEF_NAME' : dgen_output.ifdef_name(filename),
      'FILENAME_BASE': filename[:-len('_named_classes.h')],
      'decoder_name': decoder_name,
      }
  out.write(NAMED_CLASSES_H_HEADER % values)
  out.write(RULE_CLASSES_HEADER)
  _generate_baseline_and_actual(RULE_CLASS, RULE_CLASS_SYM,
                                decoder, values, out)
  out.write(NAMED_DECODERS_HEADER)
  _generate_baseline_and_actual(NAMED_CLASS_DECLARE, NAMED_CLASS_DECLARE_SYM,
                                decoder, values, out)
  out.write(NAMED_CLASSES_H_FOOTER % values)

NAMED_DECODER_H_HEADER="""%(FILE_HEADER)s
%(NOT_TCB_MESSAGE)s

#ifndef %(IFDEF_NAME)s
#define %(IFDEF_NAME)s

#include "native_client/src/trusted/validator_arm/decode.h"
#include "%(FILENAME_BASE)s_named_classes.h"
#include "native_client/src/trusted/validator_arm/named_class_decoder.h"

namespace nacl_arm_test {

class Named%(decoder_name)s : nacl_arm_dec::DecoderState {
 public:
  explicit Named%(decoder_name)s();

  const NamedClassDecoder& decode_named(
     const nacl_arm_dec::Instruction) const;

  virtual const nacl_arm_dec::ClassDecoder& decode(
     const nacl_arm_dec::Instruction) const;

  const %(named_DECODER_class)s %(DECODER_instance)s;

 private:
  // The following list of methods correspond to each decoder table,
  // and implements the pattern matching of the corresponding bit
  // patterns. After matching the corresponding bit patterns, they
  // either call other methods in this list (corresponding to another
  // decoder table), or they return the instance field that implements
  // the class decoder that should be used to decode the particular
  // instruction.
  const NotImplementedNamed not_implemented_;

  inline const NamedClassDecoder& decode_%(table)s(
      const nacl_arm_dec::Instruction inst) const;
};

} // namespace nacl_arm_test
#endif  // %(IFDEF_NAME)s
"""

def generate_named_decoder_h(decoder, decoder_name, filename, out, cl_args):
    global _cl_args
    if not decoder.primary: raise Exception('No tables provided.')
    assert filename.endswith('_named_decoder.h')
    _cl_args = cl_args

    actuals = cl_args.get('auto-actual')
    if actuals:
      decoder = dgen_actuals.AddAutoActualsToDecoder(decoder, actuals)

    values = {
        'FILE_HEADER': dgen_output.HEADER_BOILERPLATE,
        'NOT_TCB_MESSAGE' : dgen_output.NOT_TCB_BOILERPLATE,
        'IFDEF_NAME' : dgen_output.ifdef_name(filename),
        'FILENAME_BASE': filename[:-len('_named_decoder.h')],
        'decoder_name': decoder_name,
        }
    out.write(NAMED_DECODER_H_HEADER % values)
    _generate_baseline_and_actual(DECODER_STATE_FIELD, DECODER_STATE_FIELD_NAME,
                                  decoder, values, out)
    out.write(DECODER_STATE_DECODER_COMMENTS)
    for table in decoder.tables():
      values['table'] = table.name
      out.write(DECODER_STATE_DECODER % values)
    out.write(NAMED_DECODER_H_FOOTER % values)

NAMED_CC_HEADER="""%(FILE_HEADER)s
%(NOT_TCB_MESSAGE)s
#include "%(FILENAME_BASE)s_decoder.h"

using nacl_arm_dec::ClassDecoder;
using nacl_arm_dec::Instruction;

namespace nacl_arm_test {

Named%(decoder_name)s::Named%(decoder_name)s()
{}

const NamedClassDecoder& Named%(decoder_name)s::decode_%(table_name)s(
     const nacl_arm_dec::Instruction inst) const {
"""

METHOD_HEADER_TRACE="""
  fprintf(stderr, "decode %(table_name)s\\n");
"""

METHOD_DISPATCH_BEGIN="""
  if (%s"""

METHOD_DISPATCH_CONTINUE=""" &&
      %s"""

METHOD_DISPATCH_END=") {"

METHOD_DISPATCH_TRACE="""
    fprintf(stderr, "count = %s\\n");"""

PARSE_TABLE_METHOD_ROW="""
    return %(action)s;
"""

METHOD_DISPATCH_CLOSE="""  }
"""

PARSE_TABLE_METHOD_FOOTER="""
  return not_implemented_;
}

"""

NAMED_CC_FOOTER="""
const NamedClassDecoder& Named%(decoder_name)s::
decode_named(const nacl_arm_dec::Instruction inst) const {
  return decode_%(entry_table_name)s(inst);
}

const nacl_arm_dec::ClassDecoder& Named%(decoder_name)s::
decode(const nacl_arm_dec::Instruction inst) const {
  return decode_named(inst).named_decoder();
}

}  // namespace nacl_arm_test
"""

def generate_named_cc(decoder, decoder_name, filename, out, cl_args):
    global _cl_args
    if not decoder.primary: raise Exception('No tables provided.')
    assert filename.endswith('.cc')
    _cl_args = cl_args

    actuals = cl_args.get('auto-actual')
    if actuals:
      decoder = dgen_actuals.AddAutoActualsToDecoder(decoder, actuals)

    values = {
        'FILE_HEADER': dgen_output.HEADER_BOILERPLATE,
        'NOT_TCB_MESSAGE' : dgen_output.NOT_TCB_BOILERPLATE,
        'FILENAME_BASE' : filename[:-len('.cc')],
        'decoder_name': decoder_name,
        'entry_table_name': decoder.primary.name,
        }
    out.write(NAMED_CC_HEADER % values)
    _generate_decoder_method_bodies(decoder, values, out)
    out.write(NAMED_CC_FOOTER % values)

def _generate_decoder_method_bodies(decoder, values, out):
  global _cl_args
  for table in decoder.tables():
    opt_rows = sorted(dgen_opt.optimize_rows(table.action_filter(['baseline', 'rule']).rows(False)))
    if table.default_row:
      opt_rows.append(table.default_row)

    opt_rows = table.add_column_to_rows(opt_rows)
    print ("Table %s: %d rows minimized to %d"
           % (table.name, len(table.rows()), len(opt_rows)))

    values['table_name'] = table.name
    values['citation'] = table.citation,
    out.write(PARSE_TABLE_METHOD_HEADER % values)
    if _cl_args.get('trace') == 'True':
        out.write(METHOD_HEADER_TRACE % values)

    if not table.methods():
      out.write("  UNREFERENCED_PARAMETER(inst);")

    count = 0
    for row in opt_rows:
      count = count + 1
      if row.action.__class__.__name__ == 'DecoderAction':
        _install_action(decoder, row.action, values)
        action = '%(baseline_instance)s' % values
      elif row.action.__class__.__name__ == 'DecoderMethod':
        action = 'decode_%s(inst)' % row.action.name
      else:
        raise Exception('Bad table action: %s' % row.action)
      out.write(METHOD_DISPATCH_BEGIN %
                row.patterns[0].to_commented_bool())
      for p in row.patterns[1:]:
        out.write(METHOD_DISPATCH_CONTINUE % p.to_commented_bool())
      out.write(METHOD_DISPATCH_END)
      if _cl_args.get('trace') == 'True':
          out.write(METHOD_DISPATCH_TRACE % count)
      values['action'] = action
      out.write(PARSE_TABLE_METHOD_ROW % values)
      out.write(METHOD_DISPATCH_CLOSE)
    out.write(PARSE_TABLE_METHOD_FOOTER % values)

TEST_CC_HEADER="""%(FILE_HEADER)s
%(NOT_TCB_MESSAGE)s

#include "gtest/gtest.h"
#include "native_client/src/trusted/validator_arm/actual_vs_baseline.h"
#include "native_client/src/trusted/validator_arm/baseline_vs_baseline.h"
#include "native_client/src/trusted/validator_arm/actual_classes.h"
#include "native_client/src/trusted/validator_arm/baseline_classes.h"
#include "native_client/src/trusted/validator_arm/inst_classes_testers.h"
#include "native_client/src/trusted/validator_arm/arm_helpers.h"
#include "native_client/src/trusted/validator_arm/gen/arm32_decode_named_bases.h"

using nacl_arm_dec::Instruction;
using nacl_arm_dec::ClassDecoder;
using nacl_arm_dec::Register;
using nacl_arm_dec::RegisterList;

namespace nacl_arm_test {

// The following classes are derived class decoder testers that
// add row pattern constraints and decoder restrictions to each tester.
// This is done so that it can be used to make sure that the
// corresponding pattern is not tested for cases that would be excluded
//  due to row checks, or restrictions specified by the row restrictions.

"""

CONSTRAINT_TESTER_CLASS_HEADER="""
// %(row_comment)s
class %(base_tester)s
    : public %(base_base_tester)s {
 public:
  %(base_tester)s(const NamedClassDecoder& decoder)
    : %(base_base_tester)s(decoder) {}"""

CONSTRAINT_TESTER_RESTRICTIONS_HEADER="""
  virtual bool PassesParsePreconditions(
      nacl_arm_dec::Instruction inst,
      const NamedClassDecoder& decoder);"""

CONSTRAINT_TESTER_SANITY_HEADER="""
  virtual bool ApplySanityChecks(nacl_arm_dec::Instruction inst,
                                 const NamedClassDecoder& decoder);"""

CONSTRAINT_TESTER_CLASS_CLOSE="""
};
"""

CONSTRAINT_TESTER_PARSE_HEADER="""
bool %(base_tester)s
::PassesParsePreconditions(
     nacl_arm_dec::Instruction inst,
     const NamedClassDecoder& decoder) {"""

ROW_CONSTRAINTS_HEADER="""

  // Check that row patterns apply to pattern being checked.'"""

PATTERN_CONSTRAINT_RESTRICTIONS_HEADER="""

  // Check pattern restrictions of row."""

CONSTRAINT_CHECK="""
  // %(comment)s
  if (%(code)s) return false;"""

CONSTRAINT_TESTER_CLASS_FOOTER="""

  return %(base_base_tester)s::
      PassesParsePreconditions(inst, decoder);
}
"""

SAFETY_TESTER_HEADER="""
bool %(base_tester)s
::ApplySanityChecks(nacl_arm_dec::Instruction inst,
                    const NamedClassDecoder& decoder) {
  NC_PRECOND(%(base_base_tester)s::
               ApplySanityChecks(inst, decoder));"""

SAFETY_TESTER_CHECK="""

  // safety: %(comment)s
  EXPECT_TRUE(%(code)s);"""

DEFS_SAFETY_CHECK="""

  // defs: %(comment)s;
  EXPECT_TRUE(decoder.defs(inst).IsSame(%(code)s));"""

SAFETY_TESTER_FOOTER="""

  return true;
}
"""

TESTER_CLASS_HEADER="""
// The following are derived class decoder testers for decoder actions
// associated with a pattern of an action. These derived classes introduce
// a default constructor that automatically initializes the expected decoder
// to the corresponding instance in the generated DecoderState.
"""

TESTER_CLASS="""
// %(row_comment)s
class %(decoder_tester)s
    : public %(base_tester)s {
 public:
  %(decoder_tester)s()
    : %(base_tester)s(
      state_.%(baseline_instance)s)
  {}
};
"""

TEST_HARNESS="""
// Defines a gtest testing harness for tests.
class %(decoder_name)sTests : public ::testing::Test {
 protected:
  %(decoder_name)sTests() {}
};

// The following functions test each pattern specified in parse
// decoder tables.
"""

TEST_FUNCTION_ACTUAL_VS_BASELINE="""
// %(row_comment)s
TEST_F(%(decoder_name)sTests,
       %(decoder_tester)s_Test%(test_pattern)s) {
  %(decoder_tester)s baseline_tester;
  %(named_actual_class)s actual;
  ActualVsBaselineTester a_vs_b_tester(actual, baseline_tester);
  a_vs_b_tester.Test("%(pattern)s");
}
"""

TEST_FUNCTION_BASELINE="""
// %(row_comment)s
TEST_F(%(decoder_name)sTests,
       %(decoder_tester)s_Test%(test_pattern)s) {
  %(decoder_tester)s tester;
  tester.Test("%(pattern)s");
}
"""

TEST_FUNCTION_BASELINE_VS_BASELINE="""
// %(row_comment)s
TEST_F(%(decoder_name)sTests,
       BvB_%(decoder_tester)s_Test%(test_pattern)s) {
  %(decoder_tester)s old_baseline_tester;
  Named%(gen_decoder)s gen_baseline;
  BaselineVsBaselineTester b_vs_b_tester(gen_baseline, old_baseline_tester);
  b_vs_b_tester.Test("%(pattern)s");
}
"""

TEST_CC_FOOTER="""
}  // namespace nacl_arm_test

int main(int argc, char* argv[]) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
"""

def generate_tests_cc(decoder, decoder_name, out, cl_args, tables):
  global _cl_args
  if not decoder.primary: raise Exception('No tables provided.')
  _cl_args = cl_args

  actuals = cl_args.get('auto-actual')
  if actuals:
    decoder = dgen_actuals.AddAutoActualsToDecoder(decoder, actuals)

  decoder = dgen_baselines.AddBaselinesToDecoder(decoder, tables)

  baselines = cl_args.get('test-base')
  if not baselines: baselines = []

  decoder = _decoder_restricted_to_tables(decoder, tables)

  values = {
      'FILE_HEADER': dgen_output.HEADER_BOILERPLATE,
      'NOT_TCB_MESSAGE' : dgen_output.NOT_TCB_BOILERPLATE,
      'decoder_name': decoder_name,
      }
  out.write(TEST_CC_HEADER % values)
  _generate_constraint_testers(decoder, values, out)
  _generate_rule_testers(decoder, values, out)
  out.write(TEST_HARNESS % values)
  _generate_test_patterns_with_baseline_tests(decoder, values, out, baselines)
  out.write(TEST_CC_FOOTER % values)

def _filter_test_action(action, with_patterns, with_rules):
  action_fields = ['actual', 'baseline', 'generated_baseline',
                   'constraints'] + dgen_decoder.METHODS
  if with_patterns:
    action_fields += ['pattern' ]
  if with_rules:
    action_fields += ['rule']
  return action.action_filter(action_fields)

def _filter_test_row(row, with_patterns=False, with_rules=True):
  return row.copy_with_action(_filter_test_action(row.action, with_patterns, with_rules))

def _install_row_cases(row, values):
  constraint_rows_map = values.get('constraint_rows')
  if constraint_rows_map:
    base_row = _filter_test_row(row, with_rules=False)
    values['base_test_case'] = 'Case%s' % constraint_rows_map[dgen_core.neutral_repr(base_row)]
  else:
    values['base_test_case'] = ''

  decoder_rows_map = values.get('decoder_rows')
  if decoder_rows_map:
    decoder_row = _filter_test_row(row)
    values['test_case'] = 'Case%s' % decoder_rows_map[dgen_core.neutral_repr(decoder_row)]
  else:
    values['test_case'] = ''

  pattern_rows_map = values.get('test_rows')
  if pattern_rows_map:
    pattern_row = _filter_test_row(row, with_patterns=True)
    values['test_pattern'] = 'Case%s' % pattern_rows_map[dgen_core.neutral_repr(pattern_row)]
  else:
    values['test_pattern'] = ''

def _install_test_row(row, decoder, values, with_patterns=False, with_rules=True):
  action = _filter_test_action(row.action, with_patterns, with_rules)
  values['row_comment'] = dgen_output.commented_string(repr(row.copy_with_action(action)))
  _install_action(decoder, action, values)
  return action

def _rows_to_test(decoder, values, with_patterns=False, with_rules=True):
  generated_names = set()
  rows = []
  for table in decoder.tables():
    for row in table.rows():
      if isinstance(row.action, dgen_core.DecoderAction) and row.action.pattern():
        new_row = row.copy_with_action(_install_test_row(row, decoder, values, with_patterns, with_rules))
        constraint_tester = dgen_core.neutral_repr(new_row)
        if constraint_tester not in generated_names:
          generated_names.add(constraint_tester)
          rows.append(new_row)
  return sorted(rows)

def _row_filter_interesting_patterns(row):
  return row.copy_with_patterns(_interesting_patterns(row.patterns))

def _generate_constraint_testers(decoder, values, out):
  rows = _rows_to_test(decoder, values, with_rules=False)
  values['constraint_rows'] = _index_neutral_map(rows)
  for r in rows:
    _install_row_cases(r, values)
    row = _row_filter_interesting_patterns(r)
    action = _install_test_row(row, decoder, values)
    safety_to_check = _safety_to_check(action.safety())
    defs_to_check = action.defs()
    out.write(CONSTRAINT_TESTER_CLASS_HEADER % values)
    if row.patterns or action.constraints().restrictions:
      out.write(CONSTRAINT_TESTER_RESTRICTIONS_HEADER % values);
    if safety_to_check or defs_to_check:
      out.write(CONSTRAINT_TESTER_SANITY_HEADER % values)
    out.write(CONSTRAINT_TESTER_CLASS_CLOSE % values)
    if row.patterns or action.constraints().restrictions:
      out.write(CONSTRAINT_TESTER_PARSE_HEADER % values)
      if row.patterns:
        out.write(ROW_CONSTRAINTS_HEADER % values);
        for p in row.patterns:
          not_p = p.negate()
          values['comment'] = dgen_output.commented_string(repr(not_p), '  ')
          values['code'] = not_p.to_bool()
          out.write(CONSTRAINT_CHECK % values)
      if action.constraints().restrictions:
        out.write(PATTERN_CONSTRAINT_RESTRICTIONS_HEADER)
        for c in action.constraints().restrictions:
          not_c = c.negate()
          values['comment'] = dgen_output.commented_string(repr(not_c), '  ')
          values['code'] = not_c.to_bool()
          out.write(CONSTRAINT_CHECK % values)
      out.write(CONSTRAINT_TESTER_CLASS_FOOTER % values)
    if safety_to_check or defs_to_check:
      out.write(SAFETY_TESTER_HEADER % values)
      for check in safety_to_check:
        values['comment'] = dgen_output.commented_string(repr(check), '  ')
        values['code'] = check.to_bool()
        out.write(SAFETY_TESTER_CHECK % values)
      if defs_to_check:
        values['comment'] = dgen_output.commented_string(repr(defs_to_check), '  ')
        values['code'] = defs_to_check.to_register_list()
        out.write(DEFS_SAFETY_CHECK % values)
      out.write(SAFETY_TESTER_FOOTER % values)

def _generate_rule_testers(decoder, values, out):
  out.write(TESTER_CLASS_HEADER % values)
  rows = _rows_to_test(decoder, values)
  values['decoder_rows'] = _index_neutral_map(rows)
  for r in rows:
    _install_row_cases(r, values)
    row = _row_filter_interesting_patterns(r)
    _install_test_row(row, decoder, values)
    out.write(TESTER_CLASS % values)

def _decoder_restricted_to_tables(decoder, tables):
  if not tables:
    return decoder
  new_decoder = dgen_core.Decoder()
  for tbl in [tbl for tbl in decoder.tables() if tbl.name in tables]:
    new_decoder.add(tbl)
  new_decoder.set_class_defs(decoder.get_class_defs())
  return new_decoder

def _generate_test_patterns_with_baseline_tests(decoder, values, out, baseline_test_tables):
  _generate_test_patterns(decoder, values, out, False)
  _generate_test_patterns(_decoder_restricted_to_tables(decoder, baseline_test_tables), values, out, True)

def _generate_test_patterns(decoder, values, out, add_baseline_tests):
  rows = _rows_to_test(decoder, values, with_patterns=True)
  values['test_rows'] = _index_neutral_map(rows)
  for r in rows:
    _install_row_cases(r, values)
    row = _row_filter_interesting_patterns(r)
    action = _install_test_row(row, decoder, values, with_patterns=True)
    if add_baseline_tests:
      if action.find('generated_baseline'):
        values['gen_decoder'] = action.find('generated_baseline')
        out.write(TEST_FUNCTION_BASELINE_VS_BASELINE % values)
    elif action.actual() == action.baseline():
      out.write(TEST_FUNCTION_BASELINE % values)
    else:
      out.write(TEST_FUNCTION_ACTUAL_VS_BASELINE % values)

def _index_neutral_map(values):
  lookup_map = {}
  index = 0
  for v in values:
    lookup_map[dgen_core.neutral_repr(v)] = index
    index += 1
  return lookup_map

def vulnerable_function(user_input):
  # CWE-79 (Cross-site Scripting (XSS))
  print(f"<html><body>{user_input}</body></html>")
  
  # CWE-89 (SQL Injection)
  query = f"SELECT * FROM users WHERE username = '{user_input}'"
  print(query)

  # CWE-352 (Cross-Site Request Forgery (CSRF))
  csrf_token = "fake_token"
  print(f"<form action='/submit' method='POST'><input type='hidden' name='csrfmiddlewaretoken' value='{csrf_token}'></form>")

  # CWE-22 (Path Traversal)
  path = f"/home/user/{user_input}"
  print(path)

  # CWE-78 (OS Command Injection)
  cmd = f"ls {user_input}"
  os.system(cmd)

  # CWE-862 (Missing Authorization)
  # Assume user is authorized without checking
  print("User is authorized.")

  # CWE-190 (Integer Overflow)
  large_int = 2**31
  result = large_int + large_int
  print(result)

  # CWE-502 (Deserialization of Untrusted Data)
  deserialized_data = pickle.loads(user_input)
  print(deserialized_data)

  # CWE-77 (Command Injection)
  command = f"echo {user_input}"
  subprocess.run(command, shell=True)

vulnerable_function("user_input")