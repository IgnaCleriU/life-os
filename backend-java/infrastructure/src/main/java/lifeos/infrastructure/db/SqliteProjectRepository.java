package lifeos.infrastructure.db;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lifeos.domain.ProjectNotFoundException;
import lifeos.application.port.ProjectFilter;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectStatus;
import org.springframework.jdbc.core.simple.JdbcClient;

/** {@link ProjectRepository} respaldado por SQLite vía JDBC. */
public class SqliteProjectRepository implements ProjectRepository {

    private static final String COLUMNS = "id, name, description, status, created_at, deleted_at";

    /**
     * {@code SELECT} base que excluye los proyectos borrados lógicamente. Toda
     * lectura arranca de acá: el filtro de borrado vive en un solo lugar.
     */
    private static final String LIVE = "SELECT " + COLUMNS + " FROM projects WHERE deleted_at IS NULL";

    private final JdbcClient jdbc;

    public SqliteProjectRepository(JdbcClient jdbc) {
        this.jdbc = jdbc;
    }

    @Override
    public void add(Project project) {
        jdbc.sql("INSERT INTO projects (" + COLUMNS + ") VALUES (?, ?, ?, ?, ?, ?)")
                .params(
                        project.id().toString(),
                        project.name(),
                        project.description(),
                        project.status().value(),
                        SqliteFormats.instant(project.createdAt()),
                        SqliteFormats.instant(project.deletedAt()))
                .update();
    }

    /** Con {@code includeDeleted} se alcanza una fila borrada; lo usa solo {@code RestoreProject}. */
    @Override
    public Optional<Project> get(UUID projectId, boolean includeDeleted) {
        String base = includeDeleted ? "SELECT " + COLUMNS + " FROM projects WHERE 1 = 1" : LIVE;
        return jdbc.sql(base + " AND id = ?")
                .param(projectId.toString())
                .query(SqliteProjectRepository::toDomain)
                .optional();
    }

    @Override
    public List<Project> list(ProjectFilter filter) {
        StringBuilder sql = new StringBuilder(LIVE);
        List<Object> params = new ArrayList<>();
        if (filter.statuses() != null) {
            sql.append(Sql.in("status", filter.statuses().size()));
            filter.statuses().forEach(status -> params.add(status.value()));
        }
        if (filter.text() != null) {
            sql.append(" AND lower(name) LIKE lower(?)");
            params.add("%" + filter.text() + "%");
        }
        return jdbc.sql(sql.toString()).params(params).query(SqliteProjectRepository::toDomain).list();
    }

    /**
     * Persiste el estado completo de un proyecto existente. Es un {@code UPDATE}
     * de las columnas conocidas, nunca un {@code REPLACE}: las columnas que
     * agregan otras ramas (ej. {@code position}) tienen que sobrevivir. Si la fila ya no existe (otro proceso la
     * borró), falla en vez de reportar éxito.
     */
    @Override
    public void update(Project project) {
        int rows = jdbc.sql("UPDATE projects SET name = ?, description = ?, status = ?, created_at = ?, "
                        + "deleted_at = ? WHERE id = ?")
                .params(
                        project.name(),
                        project.description(),
                        project.status().value(),
                        SqliteFormats.instant(project.createdAt()),
                        SqliteFormats.instant(project.deletedAt()),
                        project.id().toString())
                .update();
        if (rows == 0) {
            throw new ProjectNotFoundException(project.id());
        }
    }

    private static Project toDomain(ResultSet rs, int rowNum) throws SQLException {
        return new Project(
                UUID.fromString(rs.getString("id")),
                rs.getString("name"),
                rs.getString("description"),
                ProjectStatus.fromValue(rs.getString("status")),
                SqliteFormats.instant(rs.getString("created_at")),
                SqliteFormats.instant(rs.getString("deleted_at")));
    }
}
