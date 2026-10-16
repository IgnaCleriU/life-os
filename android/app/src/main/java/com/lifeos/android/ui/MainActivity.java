package com.lifeos.android.ui;

import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import com.google.android.material.appbar.MaterialToolbar;
import com.lifeos.android.LifeOsApp;
import com.lifeos.android.R;

/**
 * Single activity: a top app bar (with the Settings action) over a fragment
 * container. Screens are fragments; navigate with {@link Navigator}.
 */
public class MainActivity extends AppCompatActivity implements NavigatorHost {

    private Navigator navigator;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        setSupportActionBar((MaterialToolbar) findViewById(R.id.toolbar));

        navigator = new Navigator(getSupportFragmentManager(), R.id.fragment_container);
        getSupportFragmentManager().addOnBackStackChangedListener(this::onScreenChanged);

        if (savedInstanceState == null) {
            if (LifeOsApp.from(this).settings().isConfigured()) {
                navigator.showProjects();
            } else {
                navigator.showSettingsAsRoot();
            }
        }
        onScreenChanged();
    }

    @Override
    public Navigator navigator() {
        return navigator;
    }

    private void onScreenChanged() {
        boolean canGoBack = getSupportFragmentManager().getBackStackEntryCount() > 0;
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(canGoBack);
        }
        invalidateOptionsMenu();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.main_menu, menu);
        return true;
    }

    @Override
    public boolean onPrepareOptionsMenu(Menu menu) {
        Fragment current = getSupportFragmentManager().findFragmentById(R.id.fragment_container);
        MenuItem settings = menu.findItem(R.id.action_settings);
        if (settings != null) {
            settings.setVisible(!(current instanceof SettingsFragment));
        }
        return super.onPrepareOptionsMenu(menu);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == R.id.action_settings) {
            navigator.openSettings();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    public boolean onSupportNavigateUp() {
        return navigator.back() || super.onSupportNavigateUp();
    }
}
