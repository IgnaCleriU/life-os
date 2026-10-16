package lifeos.adapters.rest;

import java.util.Map;
import lifeos.domain.DomainValidationException;
import lifeos.domain.ProjectNotEmptyException;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.TaskNotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

/**
 * Traduce excepciones de dominio y de request a respuestas con la forma uniforme
 * {@code {"error": {"code", "message"}}}, con los mismos códigos que el adapter
 * FastAPI. Los errores que FastAPI no traduce (ruta o método inexistente,
 * restricción de la base, fallo inesperado) usan códigos propios en vez del
 * formato por defecto de Spring, para que todo cliente pueda leer
 * {@code error.code}.
 */
@RestControllerAdvice
class ErrorHandler {

    private static final Logger log = LoggerFactory.getLogger(ErrorHandler.class);

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
        HttpMediaTypeNotSupportedException.class,
    })
    ResponseEntity<Map<String, Object>> requestValidation(Exception e) {
        return error(HttpStatus.UNPROCESSABLE_CONTENT, "request_validation_error", e.getMessage());
    }

    @ExceptionHandler({NoResourceFoundException.class, NoHandlerFoundException.class})
    ResponseEntity<Map<String, Object>> notFound(Exception e) {
        return error(HttpStatus.NOT_FOUND, "not_found", e.getMessage());
    }

    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    ResponseEntity<Map<String, Object>> methodNotAllowed(HttpRequestMethodNotSupportedException e) {
        return error(HttpStatus.METHOD_NOT_ALLOWED, "method_not_allowed", e.getMessage());
    }

    /** Una restricción de la base (ej. FK) que los casos de uso no anticiparon. */
    @ExceptionHandler(DataIntegrityViolationException.class)
    ResponseEntity<Map<String, Object>> integrity(DataIntegrityViolationException e) {
        return error(HttpStatus.CONFLICT, "integrity_error", e.getMostSpecificCause().getMessage());
    }

    /** Último recurso: se loguea el detalle y al cliente no se le filtra. */
    @ExceptionHandler(Exception.class)
    ResponseEntity<Map<String, Object>> unexpected(Exception e) {
        log.error("Error inesperado procesando el request", e);
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "internal_error", "Error interno");
    }

    private static ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message) {
        return ResponseEntity.status(status)
                .body(Map.of("error", Map.of("code", code, "message", message == null ? "" : message)));
    }
}
