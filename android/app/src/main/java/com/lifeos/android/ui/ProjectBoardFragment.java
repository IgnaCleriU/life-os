package com.lifeos.android.ui;

import android.os.Bundle;
import android.view.View;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import com.lifeos.android.R;

/**
 * Task board of one project. PLACEHOLDER: the Tasks-board agent replaces the
 * layout and class body (columns todo / doing / done, start / complete /
 * reopen / move / delete with Undo). Open it with {@code Navigator.openProject(id)};
 * read the id with {@link #getProjectId()}.
 */
public class ProjectBoardFragment extends BaseFragment {

    static final String TAG = "project_board";
    private static final String ARG_PROJECT_ID = "project_id";

    public static ProjectBoardFragment newInstance(String projectId) {
        ProjectBoardFragment fragment = new ProjectBoardFragment();
        Bundle args = new Bundle();
        args.putString(ARG_PROJECT_ID, projectId);
        fragment.setArguments(args);
        return fragment;
    }

    public ProjectBoardFragment() {
        super(R.layout.fragment_project_board);
    }

    /** The project this board shows. */
    public String getProjectId() {
        return requireArguments().getString(ARG_PROJECT_ID);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        TextView label = view.findViewById(R.id.placeholder_project_id);
        label.setText(getString(R.string.placeholder_board, getProjectId()));
    }

    @Override
    public void onResume() {
        super.onResume();
        setTitle(R.string.title_board);
    }
}
