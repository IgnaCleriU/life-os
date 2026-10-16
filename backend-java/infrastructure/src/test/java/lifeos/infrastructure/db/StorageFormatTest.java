package lifeos.infrastructure.db;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.file.Path;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Map;
import java.util.UUID;
import lifeos.domain.Priority;
import lifeos.domain.Project;
import lifeos.domain.ProjectStatus;
import lifeos.domain.Task;
import lifeos.domain.TaskStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/**
 * Formato de almacenamiento compartido con el backend Python (ADR 0011).
 *
 * <p>Mientras convivan, Python (MCP, CLI, TUI) y Java (REST) escriben la misma
 * base. Cada uno tiene que leer exactamente lo que escribe el otro: fechas como
 * texto naive-UTC con microsegundos, enums en minúscula y UUIDs como string.
 */
class StorageFormatTest {

    private static final String PROJECT_ID = "6f1c2b9e-3d4a-4e5f-8a7b-1c2d3e4f5a6b";
    private static final String TASK_ID = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d";

    @TempDir
    Path tmp;

    private TestDatabase db;

    @BeforeEach
    void setUp() {
        db = new TestDatabase(tmp);
    }

    @Test
    void writesProjectRowsInTheSqlalchemyFormat() {
        Project project = new Project(
                UUID.fromString(PROJECT_ID), "Life OS", null, ProjectStatus.ARCHIVED,
                Instant.parse("2026-08-01T12:29:31.480822Z"), Instant.parse("2026-08-01T13:00:00Z"));

        db.projects().add(project);

        Map<String, Object> row = db.jdbc
                .sql("SELECT id, status, created_at, deleted_at FROM projects").query().singleRow();
        assertThat(row).containsEntry("id", PROJECT_ID)
                .containsEntry("status", "archived")
                .containsEntry("created_at", "2026-08-01 12:29:31.480822")
                .containsEntry("deleted_at", "2026-08-01 13:00:00.000000");
    }

    @Test
    void writesTaskRowsInTheSqlalchemyFormat() {
        insertPythonProject();
        Task task = new Task(
                UUID.fromString(TASK_ID), UUID.fromString(PROJECT_ID), "Tarea", null,
                TaskStatus.DOING, Priority.HIGH, LocalDate.of(2026, 8, 2),
                Instant.parse("2026-08-01T12:29:31.000001Z"), null);

        db.tasks().add(task);

        Map<String, Object> row = db.jdbc
                .sql("SELECT project_id, status, priority, due_date, created_at, deleted_at FROM tasks")
                .query().singleRow();
        assertThat(row).containsEntry("project_id", PROJECT_ID)
                .containsEntry("status", "doing")
                .containsEntry("priority", "high")
                .containsEntry("due_date", "2026-08-02")
                .containsEntry("created_at", "2026-08-01 12:29:31.000001")
                .containsEntry("deleted_at", null);
    }

    @Test
    void readsRowsWrittenByPython() {
        insertPythonProject();
        db.jdbc.sql("""
                INSERT INTO tasks (id, project_id, title, description, status, priority,
                                   due_date, created_at, deleted_at)
                VALUES (?, ?, 'Tarea', NULL, 'done', 'low', '2026-08-02',
                        '2026-08-01 13:22:19.593862', NULL)
                """).params(TASK_ID, PROJECT_ID).update();

        Project project = db.projects().get(UUID.fromString(PROJECT_ID)).orElseThrow();
        Task task = db.tasks().get(UUID.fromString(TASK_ID)).orElseThrow();

        assertThat(project.createdAt()).isEqualTo(Instant.parse("2026-08-01T12:29:31.480822Z"));
        assertThat(project.status()).isSameAs(ProjectStatus.ACTIVE);
        assertThat(task.status()).isSameAs(TaskStatus.DONE);
        assertThat(task.priority()).isSameAs(Priority.LOW);
        assertThat(task.dueDate()).isEqualTo(LocalDate.of(2026, 8, 2));
        assertThat(task.createdAt()).isEqualTo(Instant.parse("2026-08-01T13:22:19.593862Z"));
    }

    @Test
    void readsTimestampsWithoutFractionalSeconds() {
        db.jdbc.sql("INSERT INTO projects (id, name, status, created_at) "
                        + "VALUES (?, 'Life OS', 'active', '2026-08-01 12:29:31')")
                .param(PROJECT_ID).update();

        assertThat(db.projects().get(UUID.fromString(PROJECT_ID)).orElseThrow().createdAt())
                .isEqualTo(Instant.parse("2026-08-01T12:29:31Z"));
    }

    @Test
    void updatesLeaveColumnsJavaDoesNotKnowUntouched() {
        // La base real ya tiene columnas de ramas sin mergear (position,
        // recurrencia). Un REPLACE o un INSERT completo las borraría.
        db.jdbc.sql("ALTER TABLE projects ADD COLUMN position INTEGER NOT NULL DEFAULT 0").update();
        db.jdbc.sql("ALTER TABLE tasks ADD COLUMN recurrence_unit TEXT").update();
        insertPythonProject();
        db.jdbc.sql("UPDATE projects SET position = 7").update();
        db.jdbc.sql("""
                INSERT INTO tasks (id, project_id, title, status, priority, created_at, recurrence_unit)
                VALUES (?, ?, 'Tarea', 'todo', 'medium', '2026-08-01 13:22:19.593862', 'week')
                """).params(TASK_ID, PROJECT_ID).update();

        Project project = db.projects().get(UUID.fromString(PROJECT_ID)).orElseThrow();
        project.rename("Renombrado");
        db.projects().update(project);
        Task task = db.tasks().get(UUID.fromString(TASK_ID)).orElseThrow();
        task.complete();
        db.tasks().update(task);

        assertThat(db.jdbc.sql("SELECT position FROM projects").query(Integer.class).single()).isEqualTo(7);
        assertThat(db.jdbc.sql("SELECT recurrence_unit FROM tasks").query(String.class).single())
                .isEqualTo("week");
        // Y una fila nueva escrita por Java toma el DEFAULT de la columna ajena.
        db.projects().add(Project.create("Nuevo", null));
        assertThat(db.jdbc.sql("SELECT count(*) FROM projects WHERE position = 0")
                        .query(Integer.class).single())
                .isEqualTo(1);
    }

    private void insertPythonProject() {
        db.jdbc.sql("INSERT INTO projects (id, name, description, status, created_at, deleted_at) "
                        + "VALUES (?, 'Life OS', NULL, 'active', '2026-08-01 12:29:31.480822', NULL)")
                .param(PROJECT_ID).update();
    }
}
