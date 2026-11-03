"""Estado del tipo de conversación a partir de los autores y los avisos del sistema.

El parser NUNCA declara que una conversación es individual: dos autores sin evidencia de grupo solo dan
`pending_confirmation` (un grupo sin avisos en el rango exportado es indistinguible de un chat 1-1)."""

REJECTED_MORE = 'rejected_more_than_two_participants'
REJECTED_FEWER = 'rejected_fewer_than_two_participants'
REJECTED_GROUP = 'rejected_possible_group'
PENDING = 'pending_confirmation'
NOT_EVALUATED = 'not_evaluated'


def conversation_state(n_authors, group_evidence):
    """(estado, advertencias). Precedencia: >2 autores, <2 autores, evidencia de grupo."""
    warnings = []
    if n_authors > 2:
        warnings.append('PARTICIPANTS_GT_2')
    if n_authors < 2:
        warnings.append('PARTICIPANTS_LT_2')
    if group_evidence:
        warnings.append('GROUP_EVIDENCE')
    if n_authors > 2:
        return REJECTED_MORE, warnings
    if n_authors < 2:
        return REJECTED_FEWER, warnings
    if group_evidence:
        return REJECTED_GROUP, warnings
    return PENDING, warnings
