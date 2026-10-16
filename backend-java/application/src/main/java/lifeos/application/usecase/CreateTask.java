package lifeos.application.usecase;

import java.time.LocalDate;
import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Priority;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.Task;

/**
 * Crea una tarea bajo un proyecto existente. La validación del título vive en
 * el dominio ({@link Task#create}).
 */
public class CreateTask {

    private final TaskRepository taskRepo;
    private final ProjectRepository projectRepo;

    public CreateTask(TaskRepository taskRepo, ProjectRepository projectRepo) {
        this.taskRepo = taskRepo;
        this.projectRepo = projectRepo;
    }

    public Task execute(
            UUID projectId, String title, Priority priority, LocalDate dueDate, String description) {
        if (projectRepo.get(projectId).isEmpty()) {
            throw new ProjectNotFoundException(projectId);
        }

        Task task = Task.create(projectId, title, priority, dueDate, description);
        taskRepo.add(task);
        return task;
    }
}
