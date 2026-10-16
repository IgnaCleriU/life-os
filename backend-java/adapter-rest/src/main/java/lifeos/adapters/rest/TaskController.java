package lifeos.adapters.rest;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import lifeos.adapters.rest.dto.TaskCreateRequest;
import lifeos.adapters.rest.dto.TaskMoveRequest;
import lifeos.adapters.rest.dto.TaskResponse;
import lifeos.application.port.TaskFilter;
import lifeos.application.usecase.CompleteTask;
import lifeos.application.usecase.CreateTask;
import lifeos.application.usecase.DeleteTask;
import lifeos.application.usecase.GetTask;
import lifeos.application.usecase.ListTasks;
import lifeos.application.usecase.MoveTask;
import lifeos.application.usecase.ReopenTask;
import lifeos.application.usecase.RestoreTask;
import lifeos.application.usecase.StartTask;
import lifeos.application.usecase.TaskUpdate;
import lifeos.application.usecase.UpdateTask;
import lifeos.domain.Priority;
import lifeos.domain.TaskStatus;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** Endpoints REST de Task, delegando en los casos de uso. */
@RestController
class TaskController {

    private final CreateTask createTask;
    private final ListTasks listTasks;
    private final GetTask getTask;
    private final UpdateTask updateTask;
    private final CompleteTask completeTask;
    private final StartTask startTask;
    private final ReopenTask reopenTask;
    private final MoveTask moveTask;
    private final DeleteTask deleteTask;
    private final RestoreTask restoreTask;

    TaskController(
            CreateTask createTask,
            ListTasks listTasks,
            GetTask getTask,
            UpdateTask updateTask,
            CompleteTask completeTask,
            StartTask startTask,
            ReopenTask reopenTask,
            MoveTask moveTask,
            DeleteTask deleteTask,
            RestoreTask restoreTask) {
        this.createTask = createTask;
        this.listTasks = listTasks;
        this.getTask = getTask;
        this.updateTask = updateTask;
        this.completeTask = completeTask;
        this.startTask = startTask;
        this.reopenTask = reopenTask;
        this.moveTask = moveTask;
        this.deleteTask = deleteTask;
        this.restoreTask = restoreTask;
    }

    /** Crea una tarea bajo un proyecto existente. */
    @PostMapping("/projects/{projectId}/tasks")
    @ResponseStatus(HttpStatus.CREATED)
    TaskResponse create(@PathVariable UUID projectId, @RequestBody TaskCreateRequest body) {
        Priority priority = body.priority() == null
                ? Priority.MEDIUM
                : RequestParsing.parse("priority", body.priority(), Priority::fromValue);
        return TaskResponse.from(createTask.execute(
                projectId,
                RequestParsing.required("title", body.title()),
                priority,
                RequestParsing.date("due_date", body.dueDate()),
                body.description()));
    }

    /** Lista las tareas de un proyecto, con los mismos filtros que {@code GET /tasks}. */
    @GetMapping("/projects/{projectId}/tasks")
    List<TaskResponse> listOfProject(
            @PathVariable UUID projectId,
            @RequestParam(name = "status", required = false) List<String> status,
            @RequestParam(name = "due_before", required = false) String dueBefore,
            @RequestParam(name = "q", required = false) String q) {
        return list(projectId, status, dueBefore, q);
    }

    /** Lista tareas de todos los proyectos, con filtros opcionales. */
    @GetMapping("/tasks")
    List<TaskResponse> listAll(
            @RequestParam(name = "project_id", required = false) String projectId,
            @RequestParam(name = "status", required = false) List<String> status,
            @RequestParam(name = "due_before", required = false) String dueBefore,
            @RequestParam(name = "q", required = false) String q) {
        return list(RequestParsing.uuid("project_id", projectId), status, dueBefore, q);
    }

    private List<TaskResponse> list(UUID projectId, List<String> status, String dueBefore, String q) {
        var filter = new TaskFilter(
                projectId,
                RequestParsing.parseAll("status", status, TaskStatus::fromValue),
                RequestParsing.date("due_before", dueBefore),
                q);
        return listTasks.execute(filter).stream().map(TaskResponse::from).toList();
    }

    /** Devuelve una tarea por id. */
    @GetMapping("/tasks/{taskId}")
    TaskResponse get(@PathVariable UUID taskId) {
        return TaskResponse.from(getTask.execute(taskId));
    }

    /**
     * Actualización parcial. Se lee el body como mapa para distinguir una clave
     * omitida (no tocar) de una en {@code null}: {@code description} y
     * {@code due_date} se limpian con null; {@code title} y {@code priority} en
     * null no hacen nada, consistente con que el dominio no los admite vacíos.
     */
    @PatchMapping("/tasks/{taskId}")
    TaskResponse update(@PathVariable UUID taskId, @RequestBody Map<String, Object> body) {
        TaskUpdate update = TaskUpdate.none()
                .withTitle(RequestParsing.patchString(body, "title"))
                .withPriority(RequestParsing.parse(
                        "priority", RequestParsing.patchString(body, "priority"), Priority::fromValue));
        if (body.containsKey("description")) {
            update = update.withDescription(RequestParsing.patchString(body, "description"));
        }
        if (body.containsKey("due_date")) {
            update = update.withDueDate(
                    RequestParsing.date("due_date", RequestParsing.patchString(body, "due_date")));
        }
        return TaskResponse.from(updateTask.execute(taskId, update));
    }

    /** Marca una tarea como completada (idempotente). */
    @PostMapping("/tasks/{taskId}/complete")
    TaskResponse complete(@PathVariable UUID taskId) {
        return TaskResponse.from(completeTask.execute(taskId));
    }

    /** Marca una tarea como en curso (idempotente). */
    @PostMapping("/tasks/{taskId}/start")
    TaskResponse start(@PathVariable UUID taskId) {
        return TaskResponse.from(startTask.execute(taskId));
    }

    /** Vuelve una tarea a pendiente (idempotente). */
    @PostMapping("/tasks/{taskId}/reopen")
    TaskResponse reopen(@PathVariable UUID taskId) {
        return TaskResponse.from(reopenTask.execute(taskId));
    }

    /** Deshace el borrado lógico de una tarea. */
    @PostMapping("/tasks/{taskId}/restore")
    TaskResponse restore(@PathVariable UUID taskId) {
        return TaskResponse.from(restoreTask.execute(taskId));
    }

    /** Mueve una tarea a otro proyecto. */
    @PostMapping("/tasks/{taskId}/move")
    TaskResponse move(@PathVariable UUID taskId, @RequestBody TaskMoveRequest body) {
        UUID projectId = RequestParsing.uuid("project_id", RequestParsing.required("project_id", body.projectId()));
        return TaskResponse.from(moveTask.execute(taskId, projectId));
    }

    /** Borra lógicamente una tarea. */
    @DeleteMapping("/tasks/{taskId}")
    ResponseEntity<Void> delete(@PathVariable UUID taskId) {
        deleteTask.execute(taskId);
        return ResponseEntity.noContent().build();
    }
}
