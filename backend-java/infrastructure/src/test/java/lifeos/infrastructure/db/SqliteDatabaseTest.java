package lifeos.infrastructure.db;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Files;
import java.nio.file.Path;
import javax.sql.DataSource;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.jdbc.core.simple.JdbcClient;

/**
 * PRAGMA por conexión y creación del esquema.
 *
 * <p>Con la base compartida (ADR 0007) varios procesos la tienen abierta a la
 * vez: WAL y {@code busy_timeout} convierten la contención en espera en vez de
 * {@code database is locked}. Se usa una base en archivo porque WAL no aplica a
 * {@code :memory:}.
 */
class SqliteDatabaseTest {

    @TempDir
    Path tmp;

    private JdbcClient open() {
        return JdbcClient.create(SqliteDatabase.open("jdbc:sqlite:" + tmp.resolve("pragmas.db")));
    }

    @Test
    void walJournalModeIsEnabled() {
        assertThat(open().sql("PRAGMA journal_mode").query(String.class).single())
                .isEqualToIgnoringCase("wal");
    }

    @Test
    void busyTimeoutIsNotZero() {
        assertThat(open().sql("PRAGMA busy_timeout").query(Integer.class).single()).isEqualTo(5000);
    }

    @Test
    void foreignKeysAreEnabled() {
        assertThat(open().sql("PRAGMA foreign_keys").query(Integer.class).single()).isEqualTo(1);
    }

    @Test
    void createsTheParentDirectoryWhenMissing() {
        Path db = tmp.resolve("no/existe/todavia/lifeos.db");

        JdbcClient.create(SqliteDatabase.open("jdbc:sqlite:" + db)).sql("SELECT 1").query().singleValue();

        assertThat(Files.isDirectory(db.getParent())).isTrue();
    }

    @Test
    void createSchemaIsIdempotentAndMatchesThePythonTables() {
        DataSource dataSource = SqliteDatabase.open("jdbc:sqlite:" + tmp.resolve("schema.db"));

        SqliteDatabase.createSchema(dataSource);
        SqliteDatabase.createSchema(dataSource);

        var names = JdbcClient.create(dataSource)
                .sql("SELECT name FROM sqlite_master WHERE type IN ('table', 'index') "
                        + "AND name NOT LIKE 'sqlite_%' ORDER BY name")
                .query(String.class)
                .list();
        assertThat(names).containsExactly(
                "ix_projects_deleted_at",
                "ix_tasks_deleted_at",
                "ix_tasks_project_id",
                "projects",
                "tasks");
    }
}
