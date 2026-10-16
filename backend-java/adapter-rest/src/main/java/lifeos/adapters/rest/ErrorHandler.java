package lifeos.adapters.rest;

import java.util.Map;
import lifeos.domain.DomainValidationException;
import lifeos.domain.ProjectNotEmptyException;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.TaskNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

/**
 * Traduce excepciones de dominio y de request a respuestas con la forma uniforme
 * {@code {"error": {"code", "message"}}}, con los mismos códigos que el adapter
 * FastAPI.
 */
@RestControllerAdvice
class ErrorHandler {

    @ExceptionHandler(DomainValidationException.class)
    ResponseEntity<Map<String, Object>> domainValidation(DomainValidationException e) {
        return error(HttpStatus.BAD_REQUEST, "domain_validation_error", e.getMessage());
    }

    @ExceptionHandler(ProjectNotFoundException.class)
    ResponseEntity<Map<String, Object>> projectNotFound(ProjectNotFoundException e) {
        return error(HttpStatus.NOT_FOUND, "project_not_found", e.getMessage());
    }

    @ExceptionHandler(TaskNotFoundException.class)
    ResponseEntity<Map<String, Object>> taskNotFound(TaskNotFoundException e) {
        return error(HttpStatus.NOT_FOUND, "task_not_found", e.getMessage());
    }

    @ExceptionHandler(ProjectNotEmptyException.class)
    ResponseEntity<Map<String, Object>> projectNotEmpty(ProjectNotEmptyException e) {
        return error(HttpStatus.CONFLICT, "project_not_empty", e.getMessage());
    }

    /**
     * Body ilegible, path o query con el tipo equivocado, o campo inválido: 422,
     * no el 400 por defecto de Spring, que chocaría con {@code domain_validation_error}.
     */
    @ExceptionHandler({
        RequestValidationException.class,
        HttpMessageNotReadableException.class,
        MethodArgumentTypeMismatchException.class,
        MissingServletRequestParameterException.class,
    })
    ResponseEntity<Map<String, Object>> requestValidation(Exception e) {
        return error(HttpStatus.UNPROCESSABLE_CONTENT, "request_validation_error", e.getMessage());
    }

    private static ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status)
                .body(Map.of("error", Map.of("code", code, "message", message == null ? "" : message)));
    }
}
