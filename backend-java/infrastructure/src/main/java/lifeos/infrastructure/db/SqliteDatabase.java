package lifeos.infrastructure.db;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.sql.DataSource;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.jdbc.support.SQLExceptionTranslator;
import org.springframework.jdbc.support.SQLStateSQLExceptionTranslator;
import org.sqlite.SQLiteConfig;
import org.sqlite.SQLiteDataSource;

/** Conexión a SQLite y creación del esquema. */
public final class SqliteDatabase {

    private static final String JDBC_PREFIX = "jdbc:sqlite:";

    /** Código primario de SQLite para violaciones de restricción (FK, NOT NULL, PK...). */
    private static final int SQLITE_CONSTRAINT = 19;

    /**
     * El mismo DDL que genera {@code SQLModel.metadata.create_all} en Python, con
     * los mismos nombres de índice: cualquiera de los dos backends puede crear la
     * base y el otro la reconoce.
     */
    private static final String[] SCHEMA = {
        """
        CREATE TABLE IF NOT EXISTS projects (
        	id VARCHAR NOT NULL,
        	name VARCHAR NOT NULL,
        	description VARCHAR,
        	status VARCHAR NOT NULL,
        	created_at DATETIME NOT NULL,
        	deleted_at DATETIME,
        	PRIMARY KEY (id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_projects_deleted_at ON projects (deleted_at)",
        """
        CREATE TABLE IF NOT EXISTS tasks (
        	id VARCHAR NOT NULL,
        	project_id VARCHAR NOT NULL,
        	title VARCHAR NOT NULL,
        	description VARCHAR,
        	status VARCHAR NOT NULL,
        	priority VARCHAR NOT NULL,
        	due_date DATE,
        	created_at DATETIME NOT NULL,
        	deleted_at DATETIME,
        	PRIMARY KEY (id),
        	FOREIGN KEY(project_id) REFERENCES projects (id)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_tasks_deleted_at ON tasks (deleted_at)",
        "CREATE INDEX IF NOT EXISTS ix_tasks_project_id ON tasks (project_id)",
    };

    private SqliteDatabase() {}

    /**
     * Abre la base con los PRAGMA que Life OS necesita en cada conexión.
     *
     * <ul>
     *   <li>{@code foreign_keys=ON}: SQLite lo trae deshabilitado; sin esto se
     *       insertan tareas con un {@code project_id} inexistente.
     *   <li>{@code journal_mode=WAL}: con la base compartida, el acceso concurrente
     *       es lo normal; WAL deja que los lectores no bloqueen al escritor.
     *   <li>{@code busy_timeout=5000}: en cero, cualquier contención revienta con
     *       {@code database is locked} en vez de esperar.
     * </ul>
     *
     * <p>Crea el directorio padre si falta: en una máquina nueva el directorio de
     * datos puede no existir todavía y SQLite no lo crea solo.
     */
    public static DataSource open(String jdbcUrl) {
        if (!jdbcUrl.startsWith(JDBC_PREFIX)) {
            throw new IllegalArgumentException("Se esperaba una URL jdbc:sqlite:, no: " + jdbcUrl);
        }
        ensureParentDirectory(jdbcUrl.substring(JDBC_PREFIX.length()));

        SQLiteConfig config = new SQLiteConfig();
        config.enforceForeignKeys(true);
        config.setJournalMode(SQLiteConfig.JournalMode.WAL);
        config.setBusyTimeout(5000);

        SQLiteDataSource dataSource = new SQLiteDataSource(config);
        dataSource.setUrl(jdbcUrl);
        return dataSource;
    }

    /**
     * {@link JdbcClient} que traduce las violaciones de restricción de SQLite a
     * {@link DataIntegrityViolationException}. Spring no trae códigos de error
     * para SQLite y las dejaría como {@code UncategorizedSQLException}.
     */
    public static JdbcClient jdbcClient(DataSource dataSource) {
        SQLExceptionTranslator fallback = new SQLStateSQLExceptionTranslator();
        JdbcTemplate template = new JdbcTemplate(dataSource);
        template.setExceptionTranslator((task, sql, ex) -> ex.getErrorCode() == SQLITE_CONSTRAINT
                ? new DataIntegrityViolationException(task + "; " + ex.getMessage(), ex)
                : fallback.translate(task, sql, ex));
        return JdbcClient.create(template);
    }

    /** Crea las tablas e índices si no existen (idempotente). */
    public static void createSchema(DataSource dataSource) {
        JdbcClient jdbc = jdbcClient(dataSource);
        for (String statement : SCHEMA) {
            jdbc.sql(statement).update();
        }
    }

    private static void ensureParentDirectory(String path) {
        if (path.isEmpty() || path.startsWith(":memory:") || path.startsWith("file:")) {
            return;
        }
        Path parent = Path.of(path).toAbsolutePath().getParent();
        try {
            Files.createDirectories(parent);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}
