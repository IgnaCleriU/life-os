package lifeos.adapters.rest;

import java.nio.file.Path;
import javax.sql.DataSource;
import lifeos.application.port.ProjectRepository;
import lifeos.application.port.TaskRepository;
import lifeos.application.usecase.ActivateProject;
import lifeos.application.usecase.ArchiveProject;
import lifeos.application.usecase.CompleteProject;
import lifeos.application.usecase.CompleteTask;
import lifeos.application.usecase.CreateProject;
import lifeos.application.usecase.CreateTask;
import lifeos.application.usecase.DeleteProject;
import lifeos.application.usecase.DeleteTask;
import lifeos.application.usecase.GetProject;
import lifeos.application.usecase.GetTask;
import lifeos.application.usecase.ListProjects;
import lifeos.application.usecase.ListTasks;
import lifeos.application.usecase.MoveTask;
import lifeos.application.usecase.ReopenTask;
import lifeos.application.usecase.RestoreProject;
import lifeos.application.usecase.RestoreTask;
import lifeos.application.usecase.StartTask;
import lifeos.application.usecase.UpdateProject;
import lifeos.application.usecase.UpdateTask;
import lifeos.infrastructure.config.DatabaseLocation;
import lifeos.infrastructure.db.SqliteDatabase;
import lifeos.infrastructure.db.SqliteProjectRepository;
import lifeos.infrastructure.db.SqliteTaskRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.simple.JdbcClient;

/**
 * Único lugar donde la implementación real (SQLite) se conecta a los casos de
 * uso. Los casos de uso no llevan anotaciones de Spring: se construyen acá, a
 * mano, igual que en {@code deps.py} del backend Python.
 */
@Configuration
public class WiringConfiguration {

    /**
     * Abre la base compartida y crea el esquema si falta (idempotente). Sin
     * {@code lifeos.database-url}, la ruta sale de {@code DATABASE_URL} o del
     * directorio de datos XDG, igual que en Python.
     */
    @Bean
    DataSource dataSource(@Value("${lifeos.database-url:}") String configuredUrl) {
        String url = configuredUrl.isBlank()
                ? DatabaseLocation.resolveDatabaseUrl(System.getenv(), Path.of(System.getProperty("user.home")))
                : configuredUrl;
        DataSource dataSource = SqliteDatabase.open(DatabaseLocation.toJdbcUrl(url));
        SqliteDatabase.createSchema(dataSource);
        return dataSource;
    }

    @Bean
    JdbcClient jdbcClient(DataSource dataSource) {
        return SqliteDatabase.jdbcClient(dataSource);
    }

    @Bean
    ProjectRepository projectRepository(JdbcClient jdbc) {
        return new SqliteProjectRepository(jdbc);
    }

    @Bean
    TaskRepository taskRepository(JdbcClient jdbc) {
        return new SqliteTaskRepository(jdbc);
    }

    // --- Project -----------------------------------------------------------

    @Bean
    CreateProject createProject(ProjectRepository projects) {
        return new CreateProject(projects);
    }

    @Bean
    ListProjects listProjects(ProjectRepository projects) {
        return new ListProjects(projects);
    }

    @Bean
    GetProject getProject(ProjectRepository projects) {
        return new GetProject(projects);
    }

    @Bean
    UpdateProject updateProject(ProjectRepository projects) {
        return new UpdateProject(projects);
    }

    @Bean
    CompleteProject completeProject(ProjectRepository projects) {
        return new CompleteProject(projects);
    }

    @Bean
    ArchiveProject archiveProject(ProjectRepository projects) {
        return new ArchiveProject(projects);
    }

    @Bean
    ActivateProject activateProject(ProjectRepository projects) {
        return new ActivateProject(projects);
    }

    @Bean
    DeleteProject deleteProject(ProjectRepository projects, TaskRepository tasks) {
        return new DeleteProject(projects, tasks);
    }

    @Bean
    RestoreProject restoreProject(ProjectRepository projects) {
        return new RestoreProject(projects);
    }

    // --- Task --------------------------------------------------------------

    @Bean
    CreateTask createTask(TaskRepository tasks, ProjectRepository projects) {
        return new CreateTask(tasks, projects);
    }

    @Bean
    ListTasks listTasks(TaskRepository tasks) {
        return new ListTasks(tasks);
    }

    @Bean
    GetTask getTask(TaskRepository tasks) {
        return new GetTask(tasks);
    }

    @Bean
    UpdateTask updateTask(TaskRepository tasks) {
        return new UpdateTask(tasks);
    }

    @Bean
    CompleteTask completeTask(TaskRepository tasks) {
        return new CompleteTask(tasks);
    }

    @Bean
    StartTask startTask(TaskRepository tasks) {
        return new StartTask(tasks);
    }

    @Bean
    ReopenTask reopenTask(TaskRepository tasks) {
        return new ReopenTask(tasks);
    }

    @Bean
    MoveTask moveTask(TaskRepository tasks, ProjectRepository projects) {
        return new MoveTask(tasks, projects);
    }

    @Bean
    DeleteTask deleteTask(TaskRepository tasks) {
        return new DeleteTask(tasks);
    }

    @Bean
    RestoreTask restoreTask(TaskRepository tasks, ProjectRepository projects) {
        return new RestoreTask(tasks, projects);
    }
}
