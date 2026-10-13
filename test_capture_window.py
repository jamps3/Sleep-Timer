import unittest
import tkinter as tk
from PIL import Image
from capture_window import padded_image
from sleep_timer_gui import parse_minutes, valid_minutes_input
from sleep_timer_gui import SleepTimerApp


class CaptureTests(unittest.TestCase):
    def test_black_padding_and_content(self):
        result = padded_image(Image.new("RGB", (3, 5), "red"), 2)
        self.assertEqual(result.size, (7, 9))
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0, 255))
        self.assertEqual(result.getpixel((2, 2)), (255, 0, 0, 255))

    def test_transparent_padding_not_transparent_content(self):
        result = padded_image(Image.new("RGB", (3, 5), "black"), 2, "transparent")
        self.assertEqual(result.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(result.getpixel((2, 2)), (0, 0, 0, 255))

    def test_negative_padding(self):
        with self.assertRaises(ValueError):
            padded_image(Image.new("RGB", (1, 1)), -1)

    def test_minutes(self):
        self.assertTrue(valid_minutes_input(""))
        self.assertEqual(parse_minutes("9999999"), 9999999)
        for value in ("", "0", "10000000", "-5", "1.5", "abc"):
            with self.assertRaises(ValueError):
                parse_minutes(value)


class TimerGuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = SleepTimerApp(self.root)
        self.app._suspend = lambda: self.fail("Tests must never suspend Windows")
        self.root.update_idletasks()

    def tearDown(self):
        self.app.abort_countdown()
        self.app.close()

    def test_actions_fit_and_largest_input(self):
        self.assertLessEqual(self.app.start_button.winfo_rooty() +
                             self.app.start_button.winfo_height(),
                             self.root.winfo_rooty() + self.root.winfo_height())
        self.app.minutes_var.set("9999999")
        self.assertEqual(self.app.start_button["state"], "normal")
        self.assertEqual(self.app.countdown["text"], "9,999,999:00")

    def test_start_cancel_and_restart(self):
        for minutes in (15, 120):
            self.app.select_preset(minutes)
            self.app.start_countdown()
            self.assertTrue(self.app.running)
            self.assertEqual(self.app.custom_entry["state"], "disabled")
            self.app.abort_countdown()
            self.assertFalse(self.app.running)
            self.assertIsNone(self.app.tick_id)
            self.assertEqual(self.app.custom_entry["state"], "normal")


if __name__ == "__main__":
    unittest.main()
