package lifeos.infrastructure.db;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import lifeos.domain.Priority;
import lifeos.domain.Project;
import lifeos.domain.ProjectStatus;
import lifeos.domain.Task;
import lifeos.domain.TaskStatus;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.junit.jupiter.api.io.TempDir;

/**
 * Ida y vuelta real contra los repositorios del backend Python (ADR 0011).
 *
 * <p>{@link StorageFormatTest} fija el formato con strings literales; este test
 * comprueba que el otro lado de verdad los entiende. Necesita {@code uv} y el
 * entorno de {@code backend/}, así que solo corre si se define
 * {@code LIFEOS_PYTHON_BACKEND} con la ruta absoluta a {@code backend/} (Maven corre cada módulo desde su propio directorio).
 */
@EnabledIfEnvironmentVariable(named = "LIFEOS_PYTHON_BACKEND", matches = ".+")
class PythonInteropTest {

    @TempDir
    Path tmp;

    @Test
    void pythonReadsWhatJavaWrites() throws Exception {
        var db = new TestDatabase(tmp);
        Project project = new Project(UUID.randomUUID(), "Desde Java", "desc", ProjectStatus.ARCHIVED,
                Instant.parse("2026-08-01T12:29:31.480822Z"), null);
        db.projects().add(project);
        Task task = new Task(UUID.randomUUID(), project.id(), "Tarea Java", null, TaskStatus.DOING,
                Priority.HIGH, LocalDate.of(2026, 8, 2), Instant.parse("2026-08-01T12:29:31.000001Z"),
                Instant.parse("2026-08-03T09:00:00Z"));
        db.tasks().add(task);

        String out = python("""
                from uuid import UUID
                from lifeos.infrastructure.db.session import get_session
                from lifeos.infrastructure.db.repositories.sqlite_project_repository import SQLiteProjectRepository
                from lifeos.infrastructure.db.repositories.sqlite_task_repository import SQLiteTaskRepository
                with get_session() as s:
                    p = SQLiteProjectRepository(s).get(UUID("%s"))
                    t = SQLiteTaskRepository(s).get(UUID("%s"), include_deleted=True)
                    print(p.name, p.status.value, p.created_at.isoformat(), sep="|")
                    print(t.title, t.status.value, t.priority.value, t.due_date.isoformat(),
                          t.created_at.isoformat(), t.deleted_at.isoformat(), sep="|")
                """.formatted(project.id(), task.id()));

        assertThat(out.lines()).containsExactly(
                "Desde Java|archived|2026-08-01T12:29:31.480822+00:00",
                "Tarea Java|doing|high|2026-08-02|2026-08-01T12:29:31.000001+00:00|2026-08-03T09:00:00+00:00");
    }

    @Test
    void javaReadsWhatPythonWrites() throws Exception {
        var db = new TestDatabase(tmp);

        List<String> out = python("""
                from datetime import date
                from lifeos.domain import Priority, Project, Task
                from lifeos.infrastructure.db.session import get_session
                from lifeos.infrastructure.db.repositories.sqlite_project_repository import SQLiteProjectRepository
                from lifeos.infrastructure.db.repositories.sqlite_task_repository import SQLiteTaskRepository
                with get_session() as s:
                    p = Project.create(name="Desde Python")
                    p.complete()
                    SQLiteProjectRepository(s).add(p)
                    t = Task.create(project_id=p.id, title="Tarea Python", priority=Priority.LOW,
                                    due_date=date(2026, 9, 1))
                    t.delete()
                    SQLiteTaskRepository(s).add(t)
                    print(p.id, p.created_at.isoformat(), sep="|")
                    print(t.id, t.created_at.isoformat(), t.deleted_at.isoformat(), sep="|")
                """).lines().toList();

        String[] p = out.get(0).split("\\|");
        String[] t = out.get(1).split("\\|");
        Project project = db.projects().get(UUID.fromString(p[0])).orElseThrow();
        Task task = db.tasks().get(UUID.fromString(t[0]), true).orElseThrow();

        assertThat(project.name()).isEqualTo("Desde Python");
        assertThat(project.status()).isSameAs(ProjectStatus.COMPLETED);
        assertThat(project.createdAt()).isEqualTo(Instant.parse(p[1].replace("+00:00", "Z")));
        assertThat(task.title()).isEqualTo("Tarea Python");
        assertThat(task.priority()).isSameAs(Priority.LOW);
        assertThat(task.dueDate()).isEqualTo(LocalDate.of(2026, 9, 1));
        assertThat(task.createdAt()).isEqualTo(Instant.parse(t[1].replace("+00:00", "Z")));
        assertThat(task.deletedAt()).isEqualTo(Instant.parse(t[2].replace("+00:00", "Z")));
        assertThat(db.tasks().get(task.id())).isEmpty();
    }

    /**
     * Corre el script con el backend Python apuntando a la base temporal del test.
     *
     * <p>La salida va a un archivo para que lo que bloquee sea {@code waitFor} con
     * timeout: leer el stdout del proceso bloquearía hasta que lo cierre, y un
     * {@code uv run} colgado dejaría trabado el job de CI.
     */
    private String python(String script) throws IOException, InterruptedException {
        Path backend = Path.of(System.getenv("LIFEOS_PYTHON_BACKEND")).toAbsolutePath();
        Path output = tmp.resolve("python-output.txt");
        var process = new ProcessBuilder("uv", "run", "--directory", backend.toString(), "python", "-c", script)
                .redirectErrorStream(true)
                .redirectOutput(output.toFile());
        process.environment().put("DATABASE_URL", "sqlite:///" + tmp.resolve("test.db"));
        Process running = process.start();
        boolean finished = running.waitFor(60, TimeUnit.SECONDS);
        if (!finished) {
            running.destroyForcibly();
        }
        String text = Files.readString(output, StandardCharsets.UTF_8);
        assertThat(finished).as("uv run no terminó en 60 s:%n%s", text).isTrue();
        assertThat(running.exitValue()).as(text).isZero();
        return text.strip();
    }
}
