// Python module wrapping basic indigo functionality
// extensible on demand

// developed by Igor Vaiman, SINP MSU, as part of TAIGA experiment

#define PY_SSIZE_T_CLEAN
#include "python3.8/Python.h"

#include <indigo/indigo_bus.h>
#include <indigo/indigo_client.h>

#include "pyindigo_ccd_client.h"


struct indigo_driver_entry *driver;  // typedef cannot be readed for some reason

PyObject* pyindigo_IndigoException;


static PyObject *shot_processing_callback = NULL;


void process_ccd_shot_with_python_callback(const void *buffer, size_t size)
{
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject *result;
    result = PyObject_CallFunction(shot_processing_callback, "y#", buffer, (Py_ssize_t)size);
    Py_XDECREF(result);

    PyGILState_Release(gstate);
}


static PyObject*
version(PyObject* self)
{
    return Py_BuildValue("s", "0.0.1");
}


static PyObject*
set_device_name(PyObject* self, PyObject* args)
{
    if (!PyArg_ParseTuple(args, "s", &ccd_device_name))
        return NULL;
    Py_RETURN_NONE;
}


static PyObject*
get_current_device_name(PyObject* self)
{
    return Py_BuildValue("s", ccd_device_name);
}


static PyObject*
check_if_device_is_connected(PyObject* self)
{
    return Py_BuildValue("i", device_connected);
}


static PyObject*
setup_ccd_client(PyObject* self, PyObject* args)
{
    indigo_set_log_level(INDIGO_LOG_INFO);
    char* ccd_driver_lib_name;
    if (!PyArg_ParseTuple(args, "s", &ccd_driver_lib_name))
        return NULL;
    indigo_start();
    indigo_attach_client(&ccd_client);
    if (indigo_load_driver(ccd_driver_lib_name, true, &driver) == INDIGO_OK)
        Py_RETURN_NONE;
    else
        return PyErr_Format(PyExc_ValueError, "Unable to load requested driver \"%s\"", ccd_driver_lib_name);
}


static PyObject*
cleanup_ccd_client(PyObject* self)
{
	indigo_device_disconnect(&ccd_client, ccd_device_name);

    /*
    this is a temporary workaround to prevent race between device disconnect and driver removal
    fix on INDIGO side is on the way!
    for discussion see https://github.com/indigo-astronomy/indigo/issues/377
    */ 
    sleep(1);
	
    
    indigo_remove_driver(driver);
	indigo_detach_client(&ccd_client);
	indigo_stop();
    Py_RETURN_NONE;
}


static PyObject*
set_shot_processing_callback(PyObject* self, PyObject* args)
{
    PyObject *new_callback = NULL;
    if (!PyArg_ParseTuple(args, "O", &new_callback))
        return NULL;
    
    if (!PyCallable_Check(new_callback)) {
        PyErr_SetString(PyExc_TypeError, "Callback must be a Python callable!");
        return NULL;
    }
    Py_XINCREF(new_callback);
    Py_XDECREF(shot_processing_callback);
    shot_processing_callback = new_callback;
    Py_RETURN_NONE;
}


static PyObject*
take_shot_with_ccd(PyObject* self, PyObject* args)
{
    float exposure;
    if (!PyArg_ParseTuple(args, "f", &exposure))
        return NULL;
    if (!shot_processing_callback) {
        return PyErr_Format(
            PyExc_ValueError,
            "No callback is stored, you must call set_shot_processing_callback at least once!"
        );
    }
    const char * items[] = { CCD_EXPOSURE_ITEM_NAME };
    double values[1] = { exposure };
    indigo_change_number_property(&ccd_client, ccd_device_name, CCD_EXPOSURE_PROPERTY_NAME, 1, items, values);
    Py_RETURN_NONE;
}


static PyObject*
set_gain(PyObject* self, PyObject* args)
{
    float gain;
    if (!PyArg_ParseTuple(args, "f", &gain))
        return NULL;
    const char * items[] = { CCD_GAIN_ITEM_NAME };
    double values[1] = { gain };
    indigo_change_number_property(&ccd_client, ccd_device_name, CCD_GAIN_PROPERTY_NAME, 1, items, values);
    Py_RETURN_NONE;
}


static PyObject*
set_ccd_mode(PyObject* self, PyObject* args)
{
    int ccd_mode;
    if (!PyArg_ParseTuple(args, "i", &ccd_mode))
        return NULL;
    char* item_name;
    switch (ccd_mode)
    {
    case 0:  // ccd_mode = 0  =>  RAW 8 1x1
        item_name = "RAW 8 1x1";
        break;
    case 1:  // ccd_mode = 0  =>  RGB 24 1x1
        item_name = "RGB 24 1x1";
        break;
    default: {item_name = "RGB 24 1x1";}
    }
    const char * items[] = { item_name };
    bool values[] = { true };
    indigo_change_switch_property(&ccd_client, ccd_device_name, CCD_MODE_PROPERTY_NAME, 1, items, values);
    Py_RETURN_NONE;
}


// Python module stuff


static PyMethodDef methods[] = {
    {"version", (PyCFunction)version, METH_NOARGS, "pyindigo core version"},
    {"set_device_name", (PyCFunction)set_device_name, METH_VARARGS, ""},
    {"get_current_device_name", (PyCFunction)get_current_device_name, METH_NOARGS, ""},
    {"check_if_device_is_connected", (PyCFunction)check_if_device_is_connected, METH_NOARGS, ""},
    {"setup_ccd_client", (PyCFunction)setup_ccd_client, METH_VARARGS, "start INDIGO bus, attach driver and devices"},
    {"cleanup_ccd_client", (PyCFunction)cleanup_ccd_client, METH_NOARGS, "detach driver and devices, stop INDIGO bus"},
    {"set_shot_processing_callback", (PyCFunction)set_shot_processing_callback, METH_VARARGS, "store new callback"},
    {"take_shot_with_exposure", (PyCFunction)take_shot_with_ccd, METH_VARARGS, "request new image from driver"},
    {"set_gain", (PyCFunction)set_gain, METH_VARARGS, "set CCD device gain"},
    {"set_ccd_mode", (PyCFunction)set_ccd_mode, METH_VARARGS, "set CCD device-specific mode"},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

static struct PyModuleDef _pyindigo = {
    PyModuleDef_HEAD_INIT,
    "_pyindigo",
    "Python interface to INDIGO operations. Used by wrapper Python code and should not be imported directly!",
    -1,
    methods
};

PyMODINIT_FUNC PyInit__pyindigo(void)
{
    pyindigo_IndigoException = PyErr_NewException("pyindigo.IndigoException", NULL, NULL);
    return PyModule_Create(&_pyindigo);
}