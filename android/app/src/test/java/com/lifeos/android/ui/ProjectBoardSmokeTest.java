package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.view.View;
import androidx.fragment.app.testing.FragmentScenario;
import androidx.recyclerview.widget.RecyclerView;
import androidx.viewpager2.widget.ViewPager2;
import com.google.android.material.tabs.TabLayout;
import com.lifeos.android.R;
import com.lifeos.android.TestApp;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/**
 * Opens the real board against a fake API. Unit tests of the helpers missed a crash on open
 * twice, so this launches the actual screen.
 */
@RunWith(RobolectricTestRunner.class)
@Config(application = TestApp.class, sdk = 35)
public class ProjectBoardSmokeTest {

    private FakeApi api;

    @Before
    public void setUp() throws Exception {
        api = new FakeApi();
        TestApp.baseUrl = api.baseUrl();
    }

    @After
    public void tearDown() throws Exception {
        api.shutdown();
    }

    private FragmentScenario<ProjectBoardFragment> launch() {
        return FragmentScenario.launchInContainer(
                ProjectBoardFragment.class,
                ProjectBoardFragment.newInstance(FakeApi.PROJECT_ID).getArguments(),
                R.style.Theme_LifeOs,
                (androidx.fragment.app.FragmentFactory) null);
    }

    private static TabLayout tabs(ProjectBoardFragment fragment) {
        return fragment.requireView().findViewById(R.id.task_board_tabs);
    }

    /** Number of task cards laid out in the To do column. */
    private static int todoCards(ProjectBoardFragment fragment) {
        ViewPager2 pager = fragment.requireView().findViewById(R.id.task_board_pager);
        RecyclerView pages = (RecyclerView) pager.getChildAt(0);
        RecyclerView.ViewHolder page = pages.findViewHolderForAdapterPosition(0);
        if (page == null) {
            return 0;
        }
        RecyclerView list = page.itemView.findViewById(R.id.task_column_list);
        return list.getAdapter() == null ? 0 : list.getChildCount();
    }

    private static void assertBoardLoaded(ProjectBoardFragment fragment) {
        TabLayout tabs = tabs(fragment);
        assertEquals(3, tabs.getTabCount());
        UiTestSupport.waitFor("tab counts", () -> {
            TabLayout.Tab first = tabs.getTabAt(0);
            return first != null && first.getText() != null && first.getText().toString().contains("2");
        });
        assertTrue(String.valueOf(tabs.getTabAt(0).getText()).contains("2"));
        assertTrue(String.valueOf(tabs.getTabAt(1).getText()).contains("1"));
        assertTrue(String.valueOf(tabs.getTabAt(2).getText()).contains("1"));
        UiTestSupport.waitFor("cards in To do", () -> todoCards(fragment) > 0);
        assertTrue(todoCards(fragment) > 0);
        View root = fragment.requireView();
        assertNotNull(root.findViewById(R.id.task_board_new));
    }

    @Test
    public void opensWithThreeTabsAndCards() {
        try (FragmentScenario<ProjectBoardFragment> scenario = launch()) {
            scenario.onFragment(ProjectBoardSmokeTest::assertBoardLoaded);
        }
    }

    @Test
    public void survivesRecreate() {
        try (FragmentScenario<ProjectBoardFragment> scenario = launch()) {
            scenario.onFragment(ProjectBoardSmokeTest::assertBoardLoaded);
            scenario.recreate();
            scenario.onFragment(ProjectBoardSmokeTest::assertBoardLoaded);
        }
    }
}
