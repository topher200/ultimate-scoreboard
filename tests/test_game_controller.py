"""Tests for GameController using real manager instances."""

from src.display_manager import (
    GENDER_MATCHUP,
    GENDER_MATCHUP_COUNTER,
    LEFT_TEAM,
    LEFT_TEAM_SCORE,
    RIGHT_TEAM,
    RIGHT_TEAM_SCORE,
)
from src.settings_store import (
    DEFAULT_SETTINGS,
    LEFT_TEAM_NAME,
    RIGHT_TEAM_NAME,
    SHOW_WMP_FRAME,
)


class TestGenderMatchupDisplay:
    """Test the gender matchup display through button presses."""

    async def test_gender_matchup_cycles_through_button_presses(
        self, game_controller, display_manager
    ):
        """Test that gender matchup cycles correctly through multiple button presses."""
        game_controller.apply_settings(DEFAULT_SETTINGS)
        game_controller.initialize_scores()

        label = display_manager._labels[GENDER_MATCHUP]
        counter_label = display_manager._labels[GENDER_MATCHUP_COUNTER]

        assert label.text == "W"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()
        assert label.text == "M"
        assert counter_label.text == "1"

        await game_controller.handle_right_score_button()
        assert label.text == "M"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()
        assert label.text == "W"
        assert counter_label.text == "1"

        await game_controller.handle_right_score_button()
        assert label.text == "W"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()
        assert label.text == "M"
        assert counter_label.text == "1"


class TestWmpFrameMarch:
    """Test which actions march the WMP frame's dashes."""

    @staticmethod
    def _marching(display_manager):
        return display_manager._wmp_frame_march_start > 0

    def test_boot_holds_dashes_still(self, game_controller, display_manager):
        game_controller.initialize_scores()

        assert not self._marching(display_manager)

    async def test_point_marches_dashes(self, game_controller, display_manager):
        await game_controller.handle_left_score_button()

        assert self._marching(display_manager)

    async def test_undo_holds_dashes_still(self, game_controller, display_manager):
        await game_controller.handle_left_score_button()
        await game_controller.handle_undo_button()

        assert not self._marching(display_manager)

    async def test_reset_holds_dashes_still(self, game_controller, display_manager):
        await game_controller.handle_left_score_button()
        await game_controller.handle_reset_button()

        assert not self._marching(display_manager)

    async def test_toggle_gender_holds_dashes_still(
        self, game_controller, display_manager
    ):
        await game_controller.handle_left_score_button()
        await game_controller.handle_toggle_gender_button()

        assert not self._marching(display_manager)


class TestGameControllerDisplayMethods:
    """Test GameController display update methods."""

    def test_set_team_names(self, game_controller, display_manager):
        """Test that set_team_names updates display correctly."""
        game_controller.set_team_names("Phoenix", "Tigers")

        left_label = display_manager._labels[LEFT_TEAM]
        right_label = display_manager._labels[RIGHT_TEAM]

        assert left_label.text == "Phoenix"
        assert right_label.text == "Tigers"

    def test_initialize_scores(self, game_controller, display_manager, score_manager):
        """Test that initialize_scores updates score display and gender matchup."""
        # Set some scores
        score_manager.left_score = 3
        score_manager.right_score = 2

        # Initialize scores
        game_controller.initialize_scores()

        # Verify scores are displayed
        left_score_label = display_manager._labels[LEFT_TEAM_SCORE]
        right_score_label = display_manager._labels[RIGHT_TEAM_SCORE]

        assert left_score_label.text == "3"
        assert right_score_label.text == "2"

        # Verify gender matchup is updated (sum=5, 5%4=1, WMP start → MMP1)
        matchup_label = display_manager._labels[GENDER_MATCHUP]
        counter_label = display_manager._labels[GENDER_MATCHUP_COUNTER]

        assert matchup_label.text == "M"
        assert counter_label.text == "1"


class TestHandleResetButton:
    """Test GameController reset button handler."""

    async def test_handle_reset_button_zeroes_display(
        self, game_controller, display_manager, score_manager
    ):
        """Test that handle_reset_button resets scores to 0-0 on display."""
        game_controller.initialize_scores()

        # Score some points
        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

        # Reset
        await game_controller.handle_reset_button()

        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

        left_label = display_manager._labels[LEFT_TEAM_SCORE]
        right_label = display_manager._labels[RIGHT_TEAM_SCORE]
        assert left_label.text == "0"
        assert right_label.text == "0"

    async def test_handle_reset_button_resets_gender_matchup(
        self, game_controller, display_manager
    ):
        """Test that after reset, gender matchup reflects score sum of 0."""
        game_controller.initialize_scores()

        # Score some points to change matchup
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        # Reset
        await game_controller.handle_reset_button()

        matchup_label = display_manager._labels[GENDER_MATCHUP]
        counter_label = display_manager._labels[GENDER_MATCHUP_COUNTER]
        assert matchup_label.text == "W"
        assert counter_label.text == "2"


class TestHandleUndoAfterReset:
    """Test GameController undo after reset."""

    async def test_undo_after_reset_restores_both_scores_on_display(
        self, game_controller, display_manager, score_manager
    ):
        """Test that undoing a reset updates both score displays."""
        game_controller.initialize_scores()

        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

        await game_controller.handle_reset_button()
        assert score_manager.left_score == 0
        assert score_manager.right_score == 0

        await game_controller.handle_undo_button()
        assert score_manager.left_score == 2
        assert score_manager.right_score == 1

        left_label = display_manager._labels[LEFT_TEAM_SCORE]
        right_label = display_manager._labels[RIGHT_TEAM_SCORE]
        assert left_label.text == "2"
        assert right_label.text == "1"


class TestGameControllerKeepsScore:
    """Test GameController keeps score."""

    def test_initialization(self, game_controller):
        """Test that GameController initializes."""
        assert game_controller is not None

    async def test_handle_multiple_button_presses(
        self, fake_matrix_portal, game_controller, score_manager
    ):
        """Test multiple button presses increment correctly."""
        # Press left button 3 times
        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()
        await game_controller.handle_left_score_button()

        # Press right button 2 times
        await game_controller.handle_right_score_button()
        await game_controller.handle_right_score_button()

        # Verify final scores
        assert score_manager.left_score == 3
        assert score_manager.right_score == 2

    def test_apply_settings_updates_display(self, display_manager, game_controller):
        """Test that apply_settings shows the team names from settings."""
        game_controller.apply_settings(
            {**DEFAULT_SETTINGS, LEFT_TEAM_NAME: "Phoenix", RIGHT_TEAM_NAME: "Tigers"}
        )

        assert display_manager._labels[LEFT_TEAM].text == "Phoenix"
        assert display_manager._labels[RIGHT_TEAM].text == "Tigers"

    def test_apply_settings_hides_frame(self, display_manager, game_controller):
        """Test that apply_settings hides the frame when SHOW_WMP_FRAME is off."""
        game_controller.initialize_scores()

        game_controller.apply_settings({**DEFAULT_SETTINGS, SHOW_WMP_FRAME: False})

        assert display_manager._wmp_frame.hidden

    async def test_toggle_gender_retries_joining_wifi(
        self, fake_network, game_controller, network_manager
    ):
        """Test that the toggle gender chord retries joining Wi-Fi."""
        fake_network.connect_error = OSError("no Wi-Fi")
        network_manager.connect()
        fake_network.connect_error = None

        await game_controller.handle_toggle_gender_button()

        assert network_manager.url is not None

    async def test_full_game_workflow(
        self, display_manager, fake_matrix_portal, game_controller, score_manager
    ):
        """Test a complete game workflow."""
        # Initialize with team names
        game_controller.apply_settings(DEFAULT_SETTINGS)
        game_controller.initialize_scores()

        # Get label references
        matchup_label = display_manager._labels[GENDER_MATCHUP]
        counter_label = display_manager._labels[GENDER_MATCHUP_COUNTER]

        # Verify initial state (0-0, sum=0) → WMP2
        assert matchup_label.text == "W"
        assert counter_label.text == "2"

        # Simulate a game with button presses
        await game_controller.handle_left_score_button()  # AWAY: 1, HOME: 0
        assert score_manager.left_score == 1
        assert score_manager.right_score == 0
        # sum=1 → MMP1
        assert matchup_label.text == "M"
        assert counter_label.text == "1"

        await game_controller.handle_right_score_button()  # AWAY: 1, HOME: 1
        assert score_manager.left_score == 1
        assert score_manager.right_score == 1
        # sum=2 → MMP2
        assert matchup_label.text == "M"
        assert counter_label.text == "2"

        await game_controller.handle_left_score_button()  # AWAY: 2, HOME: 1
        assert score_manager.left_score == 2
        assert score_manager.right_score == 1
        # sum=3 → WMP1
        assert matchup_label.text == "W"
        assert counter_label.text == "1"

        await game_controller.handle_left_score_button()  # AWAY: 3, HOME: 1
        assert score_manager.left_score == 3
        assert score_manager.right_score == 1
        # sum=4 → WMP2
        assert matchup_label.text == "W"
        assert counter_label.text == "2"


class TestPointsScored:
    async def test_counts_points_since_the_last_take(self, game_controller):
        await game_controller.handle_left_score_button()
        await game_controller.handle_right_score_button()

        assert game_controller.take_points_scored() == 2
        assert game_controller.take_points_scored() == 0
