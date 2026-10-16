package lifeos.infrastructure.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lifeos.application.port.TaskFilter;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Priority;
import lifeos.domain.Task;
import lifeos.domain.TaskStatus;
import org.springframework.jdbc.core.simple.JdbcClient;

/** {@link TaskRepository} respaldado por SQLite vía JDBC. */
public class SqliteTaskRepository implements TaskRepository {

    private static final String COLUMNS =
            "id, project_id, title, description, status, priority, due_date, created_at, deleted_at";

    /**
     * {@code SELECT} base que excluye las tareas borradas lógicamente. Es el único
     * lugar donde vive el filtro: si cada método lo escribiera por su cuenta,
     * alcanzaría con olvidarlo una vez para que reaparezcan tareas borradas.
     */
    private static final String LIVE = "SELECT " + COLUMNS + " FROM tasks WHERE deleted_at IS NULL";

    private final JdbcClient jdbc;

    public SqliteTaskRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public void add(Task task) {
        jdbc.sql("INSERT INTO tasks (" + COLUMNS + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)")
                .params(
                        task.id().toString(),
                        task.projectId().toString(),
                        task.title(),
                        task.description(),
                        task.status().value(),
                        task.priority().value(),
                        SqliteFormats.date(task.dueDate()),
                        SqliteFormats.instant(task.createdAt()),
                        SqliteFormats.instant(task.deletedAt()))
                .update();
    }

    /** Con {@code includeDeleted} se alcanza una fila borrada; lo usa solo {@code RestoreTask}. */
    @Override
    public Optional<Task> get(UUID taskId, boolean includeDeleted) {
        String base = includeDeleted ? "SELECT " + COLUMNS + " FROM tasks WHERE 1 = 1" : LIVE;
        return jdbc.sql(base + " AND id = ?")
                .param(taskId.toString())
                .query(SqliteTaskRepository::toDomain)
                .optional();
    }

    @Override
    public List<Task> list(TaskFilter filter) {
        StringBuilder sql = new StringBuilder(LIVE);
        List<Object> params = new ArrayList<>();
        if (filter.projectId() != null) {
            sql.append(" AND project_id = ?");
            params.add(filter.projectId().toString());
        }
        if (filter.statuses() != null) {
            sql.append(Sql.in("status", filter.statuses().size()));
            filter.statuses().forEach(status -> params.add(status.value()));
        }
        if (filter.dueBefore() != null) {
            // `IS NOT NULL` es redundante en SQL, pero deja explícito que "vence
            // antes de X" no incluye a las tareas sin fecha.
            sql.append(" AND due_date IS NOT NULL AND due_date <= ?");
            params.add(SqliteFormats.date(filter.dueBefore()));
        }
        if (filter.text() != null) {
            sql.append(" AND lower(title) LIKE lower(?)");
            params.add("%" + filter.text() + "%");
        }
        return jdbc.sql(sql.toString()).params(params).query(SqliteTaskRepository::toDomain).list();
    }

    /**
     * Persiste el estado completo de una tarea existente con un {@code UPDATE} de
     * las columnas conocidas, nunca un {@code REPLACE}: las columnas que agregan
     * otras ramas (ej. recurrencia) tienen que sobrevivir.
     */
    @Override
    public void update(Task task) {
        jdbc.sql("UPDATE tasks SET project_id = ?, title = ?, description = ?, status = ?, "
                        + "priority = ?, due_date = ?, created_at = ?, deleted_at = ? WHERE id = ?")
                .params(
                        task.projectId().toString(),
                        task.title(),
                        task.description(),
                        task.status().value(),
                        task.priority().value(),
                        SqliteFormats.date(task.dueDate()),
                        SqliteFormats.instant(task.createdAt()),
                        SqliteFormats.instant(task.deletedAt()),
                        task.id().toString())
                .update();
    }

    private static Task toDomain(ResultSet rs, int rowNum) throws SQLException {
        return new Task(
                UUID.fromString(rs.getString("id")),
                UUID.fromString(rs.getString("project_id")),
                rs.getString("title"),
                rs.getString("description"),
                TaskStatus.fromValue(rs.getString("status")),
                Priority.fromValue(rs.getString("priority")),
                SqliteFormats.date(rs.getString("due_date")),
                SqliteFormats.instant(rs.getString("created_at")),
                SqliteFormats.instant(rs.getString("deleted_at")));
    }
}
