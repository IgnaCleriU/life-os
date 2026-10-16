package com.lifeos.android.ui;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import androidx.fragment.app.testing.FragmentScenario;
import androidx.recyclerview.widget.RecyclerView;
import com.lifeos.android.R;
import com.lifeos.android.TestApp;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

/** Opens the real projects screen against a fake API and checks it lists the project. */
@RunWith(RobolectricTestRunner.class)
@Config(application = TestApp.class, sdk = 35)
public class ProjectsSmokeTest {

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

    private static int rows(ProjectsFragment fragment) {
        RecyclerView list = fragment.requireView().findViewById(R.id.projects_list);
        return list.getAdapter() == null ? 0 : list.getAdapter().getItemCount();
    }

    @Test
    public void opensAndListsTheProject() {
        try (FragmentScenario<ProjectsFragment> scenario =
                     FragmentScenario.launchInContainer(ProjectsFragment.class, null, R.style.Theme_LifeOs,
                             (androidx.fragment.app.FragmentFactory) null)) {
            scenario.onFragment(fragment -> {
                UiTestSupport.waitFor("project rows", () -> rows(fragment) > 0);
                assertTrue(rows(fragment) > 0);
            });
            scenario.recreate();
            scenario.onFragment(fragment -> {
                UiTestSupport.waitFor("project rows after recreate", () -> rows(fragment) > 0);
                assertEquals(true, rows(fragment) > 0);
            });
        }
    }
}
