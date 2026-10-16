package com.lifeos.android.ui;

import androidx.annotation.IdRes;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentTransaction;

/**
 * The only place that knows how screens are swapped. Screens are fragments in
 * {@code MainActivity}'s container; adding a screen means adding a method here
 * (or calling {@link #push}) and nothing else in the shell.
 */
public final class Navigator {

    private final FragmentManager fragmentManager;
    @IdRes private final int containerId;

    Navigator(FragmentManager fragmentManager, @IdRes int containerId) {
        this.fragmentManager = fragmentManager;
        this.containerId = containerId;
    }

    /** The navigator of the activity hosting {@code fragment}. */
    public static Navigator from(Fragment fragment) {
        return ((NavigatorHost) fragment.requireActivity()).navigator();
    }

    /** Resets the stack to the projects list (the start destination). */
    public void showProjects() {
        fragmentManager.popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE);
        fragmentManager.beginTransaction()
                .replace(containerId, new ProjectsFragment(), ProjectsFragment.TAG)
                .commit();
    }

    /** Pushes the task board of a project. */
    public void openProject(String projectId) {
        push(ProjectBoardFragment.newInstance(projectId), ProjectBoardFragment.TAG);
    }

    /** Pushes Settings unless it is already showing. */
    public void openSettings() {
        if (fragmentManager.findFragmentByTag(SettingsFragment.TAG) == null) {
            push(new SettingsFragment(), SettingsFragment.TAG);
        }
    }

    /** First run: Settings is the root screen, with nothing to go back to. */
    public void showSettingsAsRoot() {
        fragmentManager.popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE);
        fragmentManager.beginTransaction()
                .replace(containerId, new SettingsFragment(), SettingsFragment.TAG)
                .commit();
    }

    /** Pops the current screen. Returns false if it was the root. */
    public boolean back() {
        if (fragmentManager.getBackStackEntryCount() > 0) {
            fragmentManager.popBackStack();
            return true;
        }
        return false;
    }

    /** Pushes any fragment on the back stack: the extension point for new screens. */
    public void push(Fragment fragment, String tag) {
        fragmentManager.beginTransaction()
                .setTransition(FragmentTransaction.TRANSIT_FRAGMENT_OPEN)
                .replace(containerId, fragment, tag)
                .addToBackStack(tag)
                .commit();
    }
}
