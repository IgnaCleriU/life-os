package lifeos.adapters.rest;

import java.util.List;
import java.util.Map;
import java.util.UUID;
import lifeos.adapters.rest.dto.ProjectCreateRequest;
import lifeos.adapters.rest.dto.ProjectResponse;
import lifeos.application.Change;
import lifeos.application.port.ProjectFilter;
import lifeos.application.usecase.ActivateProject;
import lifeos.application.usecase.ArchiveProject;
import lifeos.application.usecase.CompleteProject;
import lifeos.application.usecase.CreateProject;
import lifeos.application.usecase.DeleteProject;
import lifeos.application.usecase.GetProject;
import lifeos.application.usecase.ListProjects;
import lifeos.application.usecase.RestoreProject;
import lifeos.application.usecase.UpdateProject;
import lifeos.domain.ProjectStatus;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

/** Endpoints REST de Project, delegando en los casos de uso. */
@RestController
@RequestMapping("/projects")
class ProjectController {

    private final CreateProject createProject;
    private final ListProjects listProjects;
    private final GetProject getProject;
    private final UpdateProject updateProject;
    private final CompleteProject completeProject;
    private final ArchiveProject archiveProject;
    private final ActivateProject activateProject;
    private final DeleteProject deleteProject;
    private final RestoreProject restoreProject;

    ProjectController(
            CreateProject createProject,
            ListProjects listProjects,
            GetProject getProject,
            UpdateProject updateProject,
            CompleteProject completeProject,
            ArchiveProject archiveProject,
            ActivateProject activateProject,
            DeleteProject deleteProject,
            RestoreProject restoreProject) {
        this.createProject = createProject;
        this.listProjects = listProjects;
        this.getProject = getProject;
        this.updateProject = updateProject;
        this.completeProject = completeProject;
        this.archiveProject = archiveProject;
        this.activateProject = activateProject;
        this.deleteProject = deleteProject;
        this.restoreProject = restoreProject;
    }

    /** Crea un proyecto nuevo. */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    ProjectResponse create(@RequestBody ProjectCreateRequest body) {
        return ProjectResponse.from(
                createProject.execute(RequestParsing.required("name", body.name()), body.description()));
    }

    /** Lista los proyectos, opcionalmente filtrados por estado (repetible) y/o texto. */
    @GetMapping
    List<ProjectResponse> list(
            @RequestParam(name = "status", required = false) List<String> status,
            @RequestParam(name = "q", required = false) String q) {
        var filter = new ProjectFilter(RequestParsing.parseAll("status", status, ProjectStatus::fromValue), q);
        return listProjects.execute(filter).stream().map(ProjectResponse::from).toList();
    }

    /** Devuelve un proyecto por id. */
    @GetMapping("/{projectId}")
    ProjectResponse get(@PathVariable UUID projectId) {
        return ProjectResponse.from(getProject.execute(projectId));
    }

    /**
     * Actualización parcial. Se lee el body como mapa para distinguir una clave
     * omitida (no tocar) de una en {@code null} (limpiar la descripción). Un
     * {@code name} en null no hace nada: el dominio no admite un nombre vacío.
     */
    @PatchMapping("/{projectId}")
    ProjectResponse update(@PathVariable UUID projectId, @RequestBody Map<String, Object> body) {
        String name = RequestParsing.patchString(body, "name");
        Change<String> description = body.containsKey("description")
                ? Change.to(RequestParsing.patchString(body, "description"))
                : Change.unset();
        return ProjectResponse.from(updateProject.execute(projectId, name, description));
    }

    /** Marca un proyecto como finalizado (idempotente). */
    @PostMapping("/{projectId}/complete")
    ProjectResponse complete(@PathVariable UUID projectId) {
        return ProjectResponse.from(completeProject.execute(projectId));
    }

    /** Archiva un proyecto (idempotente). */
    @PostMapping("/{projectId}/archive")
    ProjectResponse archive(@PathVariable UUID projectId) {
        return ProjectResponse.from(archiveProject.execute(projectId));
    }

    /** Reactiva un proyecto (idempotente). */
    @PostMapping("/{projectId}/activate")
    ProjectResponse activate(@PathVariable UUID projectId) {
        return ProjectResponse.from(activateProject.execute(projectId));
    }

    /** Deshace el borrado lógico de un proyecto. */
    @PostMapping("/{projectId}/restore")
    ProjectResponse restore(@PathVariable UUID projectId) {
        return ProjectResponse.from(restoreProject.execute(projectId));
    }

    /** Borra lógicamente un proyecto; falla si todavía tiene tareas vivas. */
    @DeleteMapping("/{projectId}")
    ResponseEntity<Void> delete(@PathVariable UUID projectId) {
        deleteProject.execute(projectId);
        return ResponseEntity.noContent().build();
    }
}
