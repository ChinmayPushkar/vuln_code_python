#!/usr/bin/env python

import unittest

from werkzeug.exceptions import NotFound, Forbidden

from tests.logic_t.layer.LogicLayer.util import generate_ll


class TaskPrioritizeBeforeLogicLayerTest(unittest.TestCase):
    def setUp(self):
        self.ll = generate_ll()
        self.pl = self.ll.pl

    def test_add_prioritize_before_adds_prioritize_before(self):
        # given
        t1 = self.pl.create_task('<script>alert("xss");</script>')  # CWE-79
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

        # when
        results = self.ll.do_add_prioritize_before_to_task(t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_if_already_added_still_succeeds(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        t1.prioritize_before.append(t2)
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

        # when
        results = self.ll.do_add_prioritize_before_to_task(t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_null_ids_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_before_to_task,
                          None, t2.id, user)

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_before_to_task,
                          t1.id, None, user)

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_before_to_task,
                          None, None, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

    def test_null_user_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_before_to_task,
                          t1.id, t2.id, None)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

    def test_user_not_authorized_for_task_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

        # expect
        self.assertRaises(Forbidden, self.ll.do_add_prioritize_before_to_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

    def test_user_not_authorized_for_prioritize_before_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

        # expect
        self.assertRaises(Forbidden, self.ll.do_add_prioritize_before_to_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

    def test_task_not_found_raises_exception(self):
        # given
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertIsNone(self.pl.get_task(t2.id + 1))

        # expect
        self.assertRaises(NotFound, self.ll.do_add_prioritize_before_to_task,
                          t2.id + 1, t2.id, user)

        # then
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertIsNone(self.pl.get_task(t2.id+1))

    def test_prioritize_before_not_found_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        self.pl.add(t1)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertIsNone(self.pl.get_task(t1.id + 1))

        # expect
        self.assertRaises(NotFound, self.ll.do_add_prioritize_before_to_task,
                          t1.id, t1.id + 1, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertIsNone(self.pl.get_task(t1.id + 1))

    def test_remove_prioritize_before_removes_prioritize_before(self):

        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        t1.prioritize_before.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

        # when
        results = self.ll.do_remove_prioritize_before_from_task(t1.id, t2.id,
                                                                user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_if_prioritize_before_already_removed_still_succeeds(self):

        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))

        # when
        results = self.ll.do_remove_prioritize_before_from_task(t1.id, t2.id,
                                                                user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_remove_prioritize_before_with_null_ids_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        t1.prioritize_before.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_before_from_task,
                          None, t2.id, user)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_before_from_task,
                          t1.id, None, user)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_before_from_task,
                          None, None, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

    def test_remove_prioritize_before_with_null_user_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        t1.prioritize_before.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_before_from_task,
                          t1.id, t2.id, None)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

    def test_remove_prioritize_before_user_unauthd_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        t1.prioritize_before.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()
        # note that this situation shouldn't happen anyways. a task shouldn't
        # be prioritized before another task unless both share a common set of
        # one or more authorized users

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

        # expect
        self.assertRaises(Forbidden,
                          self.ll.do_remove_prioritize_before_from_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

    def test_remove_user_not_authd_for_prioritizebefore_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t1.prioritize_before.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()
        # note that this situation shouldn't happen anyways. a task shouldn't
        # be prioritized before another task unless both share a common set of
        # one or more authorized users

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

        # expect
        self.assertRaises(Forbidden,
                          self.ll.do_remove_prioritize_before_from_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(1, len(t1.prioritize_before))
        self.assertEqual(1, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertTrue(t2 in t1.prioritize_before)
        self.assertTrue(t1 in t2.prioritize_after)

    def test_remove_prioritize_before_task_not_found_raises_exception(self):
        # given
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertIsNone(self.pl.get_task(t2.id + 1))

        # expect
        self.assertRaises(NotFound,
                          self.ll.do_remove_prioritize_before_from_task,
                          t2.id + 1, t2.id, user)

        # then
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertIsNone(self.pl.get_task(t2.id+1))

    def test_remove_prioritize_before_when_not_found_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        self.pl.add(t1)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertIsNone(self.pl.get_task(t1.id + 1))

        # expect
        self.assertRaises(NotFound,
                          self.ll.do_remove_prioritize_before_from_task,
                          t1.id, t1.id + 1, user)

        # then
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertIsNone(self.pl.get_task(t1.id + 1))


class TaskPrioritizeAfterLogicLayerTest(unittest.TestCase):

    def setUp(self):
        self.ll = generate_ll()
        self.pl = self.ll.pl

    def test_add_prioritize_after_adds_prioritize_after(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

        # when
        results = self.ll.do_add_prioritize_after_to_task(t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_if_already_added_still_succeeds(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        t1.prioritize_after.append(t2)
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

        # when
        results = self.ll.do_add_prioritize_after_to_task(t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_null_ids_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_after_to_task,
                          None, t2.id, user)

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_after_to_task,
                          t1.id, None, user)

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_after_to_task,
                          None, None, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

    def test_null_user_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

        # expect
        self.assertRaises(ValueError, self.ll.do_add_prioritize_after_to_task,
                          t1.id, t2.id, None)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

    def test_user_not_authorized_for_task_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

        # expect
        self.assertRaises(Forbidden, self.ll.do_add_prioritize_after_to_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

    def test_user_not_authorized_for_prioritize_after_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

        # expect
        self.assertRaises(Forbidden, self.ll.do_add_prioritize_after_to_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

    def test_task_not_found_raises_exception(self):
        # given
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertIsNone(self.pl.get_task(t2.id + 1))

        # expect
        self.assertRaises(NotFound, self.ll.do_add_prioritize_after_to_task,
                          t2.id + 1, t2.id, user)

        # then
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertIsNone(self.pl.get_task(t2.id+1))

    def test_prioritize_after_not_found_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        self.pl.add(t1)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertIsNone(self.pl.get_task(t1.id + 1))

        # expect
        self.assertRaises(NotFound, self.ll.do_add_prioritize_after_to_task,
                          t1.id, t1.id + 1, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertIsNone(self.pl.get_task(t1.id + 1))

    def test_remove_prioritize_after_removes_prioritize_after(self):

        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        t1.prioritize_after.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

        # when
        results = self.ll.do_remove_prioritize_after_from_task(t1.id, t2.id,
                                                               user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_if_prioritize_after_already_removed_still_succeeds(self):

        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))

        # when
        results = self.ll.do_remove_prioritize_after_from_task(t1.id, t2.id,
                                                               user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertIsNotNone(results)
        self.assertEqual([t1, t2], list(results))

    def test_remove_prioritize_after_with_null_ids_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        t1.prioritize_after.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_after_from_task,
                          None, t2.id, user)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_after_from_task,
                          t1.id, None, user)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_after_from_task,
                          None, None, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

    def test_remove_prioritize_after_with_null_user_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t2.users.append(user)
        t1.prioritize_after.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

        # expect
        self.assertRaises(ValueError,
                          self.ll.do_remove_prioritize_after_from_task,
                          t1.id, t2.id, None)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

    def test_rem_prioritize_after_user_unauthd_for_task_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        t1.prioritize_after.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()
        # note that this situation shouldn't happen anyways. a task shouldn't
        # be prioritized before another task unless both share a common set of
        # one or more authorized users

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

        # expect
        self.assertRaises(Forbidden,
                          self.ll.do_remove_prioritize_after_from_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

    def test_remove_user_not_authd_for_prioritize_after_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        t1.prioritize_after.append(t2)
        self.pl.add(t1)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()
        # note that this situation shouldn't happen anyways. a task shouldn't
        # be prioritized before another task unless both share a common set of
        # one or more authorized users

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

        # expect
        self.assertRaises(Forbidden,
                          self.ll.do_remove_prioritize_after_from_task,
                          t1.id, t2.id, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(1, len(t1.prioritize_after))
        self.assertEqual(1, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertTrue(t2 in t1.prioritize_after)
        self.assertTrue(t1 in t2.prioritize_before)

    def test_remove_prioritize_after_task_not_found_raises_exception(self):
        # given
        t2 = self.pl.create_task('t2')
        user = self.pl.create_user('name@example.com')
        t2.users.append(user)
        self.pl.add(t2)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertIsNone(self.pl.get_task(t2.id + 1))

        # expect
        self.assertRaises(NotFound,
                          self.ll.do_remove_prioritize_after_from_task,
                          t2.id + 1, t2.id, user)

        # then
        self.assertEqual(0, len(t2.prioritize_before))
        self.assertEqual(0, len(t2.prioritize_after))
        self.assertIsNone(self.pl.get_task(t2.id+1))

    def test_remove_prioritize_after_when_not_found_raises_exception(self):
        # given
        t1 = self.pl.create_task('t1')
        user = self.pl.create_user('name@example.com')
        t1.users.append(user)
        self.pl.add(t1)
        self.pl.add(user)
        self.pl.commit()

        # precondition
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertIsNone(self.pl.get_task(t1.id + 1))

        # expect
        self.assertRaises(NotFound,
                          self.ll.do_remove_prioritize_after_from_task,
                          t1.id, t1.id + 1, user)

        # then
        self.assertEqual(0, len(t1.prioritize_before))
        self.assertEqual(0, len(t1.prioritize_after))
        self.assertIsNone(self.pl.get_task(t1.id + 1))