package com.lifeos.android.ui;

import android.view.View;
import android.widget.Button;
import com.lifeos.android.R;

/**
 * Start destination. PLACEHOLDER: the Projects-screens agent replaces this
 * layout and class body with the real list (RecyclerView + SwipeRefreshLayout,
 * create / edit / complete / archive / delete with Undo). Keep the class name,
 * {@link #TAG} and the no-arg constructor: {@link Navigator} depends on them.
 */
public class ProjectsFragment extends BaseFragment {

    static final String TAG = "projects";

    public ProjectsFragment() {
        super(R.layout.fragment_projects);
    }

    @Override
    public void onViewCreated(View view, android.os.Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        // Placeholder wiring so the navigation path is exercisable: remove with the real screen.
        Button open = view.findViewById(R.id.placeholder_open_board);
        open.setOnClickListener(v -> navigator().openProject("00000000-0000-0000-0000-000000000000"));
    }

    @Override
    public void onResume() {
        super.onResume();
        setTitle(R.string.title_projects);
    }
}
